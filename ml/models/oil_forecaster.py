from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from ml.features.oil_features import build_oil_features, clean_oil_price_data


SERIES_ALIASES: Dict[str, str] = {
    "brent": "RBRTE",
    "rbrte": "RBRTE",
    "wti": "RWTC",
    "rwtc": "RWTC",
}

SUPPORTED_HORIZONS: List[int] = [7, 30, 90]


@dataclass
class ForecastMetrics:
    """Evaluation metrics for price forecasting."""
    mae: float
    rmse: float
    r2: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "r2": round(self.r2, 4),
        }


@dataclass
class ModelComparisonResult:
    """Holds comparative evaluation between ML model and persistence baseline."""
    horizon_days: int
    series: str
    sample_count_train: int
    sample_count_test: int
    train_end_date: str
    test_start_date: str
    test_end_date: str
    xgboost_metrics: ForecastMetrics
    baseline_metrics: ForecastMetrics
    outperformed_baseline: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "series": self.series,
            "horizon_days": self.horizon_days,
            "train_samples": self.sample_count_train,
            "test_samples": self.sample_count_test,
            "train_end_date": self.train_end_date,
            "test_start_date": self.test_start_date,
            "test_end_date": self.test_end_date,
            "xgboost": self.xgboost_metrics.to_dict(),
            "baseline_persistence": self.baseline_metrics.to_dict(),
            "outperformed_baseline": self.outperformed_baseline,
        }


class OilPriceForecaster:
    """
    Production pipeline for forecasting Brent and WTI crude oil prices.

    Key Architectural Principles:
    1. Stationary Modeling: Forecasts multi-period forward returns R_{t, t+h},
       then maps to predicted price P_{t+h} = P_t * (1 + R_{t, t+h}).
    2. Strict Anti-Leakage:
       - Strictly trailing features at time t.
       - Pure chronological time-series splitting (NO random shuffling).
       - Purged gap between train labels and test features to prevent label overlap.
       - Feature scalers fit strictly on training set only.
    3. Benchmark Comparison: Evaluated alongside Random Walk / Persistence baseline
       (P_{t+h} = P_t).
    """

    def __init__(
        self,
        series: str = "RBRTE",
        horizon_days: int = 7,
        n_estimators: int = 150,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        random_state: int = 42,
    ):
        normalized_series = SERIES_ALIASES.get(series.lower(), series.upper())
        if normalized_series not in ["RBRTE", "RWTC"]:
            raise ValueError(f"Unsupported oil series '{series}'. Expected 'RBRTE' (Brent) or 'RWTC' (WTI).")

        if horizon_days not in SUPPORTED_HORIZONS:
            raise ValueError(f"Unsupported horizon {horizon_days}. Expected one of {SUPPORTED_HORIZONS} days.")

        self.series = normalized_series
        self.horizon_days = horizon_days
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.feature_cols: List[str] = []
        self.is_fitted = False
        self.last_observed_date: Optional[pd.Timestamp] = None
        self.last_observed_price: Optional[float] = None

    def _prepare_features_and_targets(
        self,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Builds features and aligns forward-looking target without lookahead bias in features.

        :return: (X_features, y_target_return, y_target_price)
        """
        cleaned = clean_oil_price_data(df)
        series_df = cleaned[cleaned["series"] == self.series].sort_values("period").reset_index(drop=True)

        min_samples = 40 + self.horizon_days
        if len(series_df) < min_samples:
            raise ValueError(
                f"Insufficient historical data for series '{self.series}' at horizon {self.horizon_days}d. "
                f"Found {len(series_df)} records, minimum required is {min_samples}."
            )

        # 1. Trailing engineered features (no future info)
        feat_df = build_oil_features(series_df)

        # 2. Forward target (strictly isolated)
        price = feat_df["value"]
        future_price = price.shift(-self.horizon_days)
        target_return = (future_price - price) / price

        # Candidate feature columns: drop identifier, target, and date columns
        exclude_cols = [
            "period", "series", "source", "value", "units", "series_description"
        ]
        feature_cols = [c for c in feat_df.columns if c not in exclude_cols]

        # Valid rows where both features and target exist (drop the last `horizon_days` rows)
        valid_idx = target_return.dropna().index
        # Also drop initial rows with NaNs from feature lookbacks
        valid_df = feat_df.loc[valid_idx].copy()
        valid_targets = target_return.loc[valid_idx]
        valid_future_prices = future_price.loc[valid_idx]

        # Remove any rows with NaN in features
        feature_matrix = valid_df[feature_cols].copy()
        clean_mask = feature_matrix.notna().all(axis=1)

        X = feature_matrix.loc[clean_mask]
        y_return = valid_targets.loc[clean_mask]
        y_price = valid_future_prices.loc[clean_mask]
        current_price = valid_df.loc[clean_mask, "value"]
        dates = valid_df.loc[clean_mask, "period"]

        X.insert(0, "_current_price", current_price)
        X.insert(0, "_period", dates)

        return X, y_return, y_price

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
    ) -> ModelComparisonResult:
        """
        Executes strict time-series train/test split, fits model, and evaluates against
        persistence baseline.
        """
        X_all, y_return_all, y_price_all = self._prepare_features_and_targets(df)

        n_samples = len(X_all)
        n_test = int(np.floor(n_samples * test_size))
        min_test_size = 10
        if n_test < min_test_size:
            raise ValueError(
                f"Dataset too small for reliable time-series validation: test size has {n_test} samples "
                f"(minimum {min_test_size} required)."
            )

        n_train = n_samples - n_test

        # Temporal split (strictly chronological)
        train_idx = np.arange(0, n_train)
        test_idx = np.arange(n_train, n_samples)

        # Apply purge gap: remove the last (horizon_days) observations from training set
        # to ensure training targets do not overlap with test feature windows
        purge_gap = max(0, min(self.horizon_days, int(n_train * 0.2)))
        train_idx_purged = train_idx[:-purge_gap] if purge_gap > 0 else train_idx

        # Separate metadata from feature columns
        metadata_cols = ["_period", "_current_price"]
        feature_cols = [c for c in X_all.columns if c not in metadata_cols]
        self.feature_cols = feature_cols

        X_train_raw = X_all.iloc[train_idx_purged][feature_cols]
        y_train_return = y_return_all.iloc[train_idx_purged]

        X_test_raw = X_all.iloc[test_idx][feature_cols]
        y_test_price = y_price_all.iloc[test_idx]
        test_current_price = X_all.iloc[test_idx]["_current_price"]

        train_end_date = str(X_all.iloc[train_idx_purged]["_period"].max().date())
        test_start_date = str(X_all.iloc[test_idx]["_period"].min().date())
        test_end_date = str(X_all.iloc[test_idx]["_period"].max().date())

        # Fit scaler ONLY on training data
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_test_scaled = self.scaler.transform(X_test_raw)

        # Fit XGBoost model
        self.model.fit(X_train_scaled, y_train_return)
        self.is_fitted = True

        # Generate model predictions
        pred_returns = self.model.predict(X_test_scaled)
        pred_prices_xgb = test_current_price.values * (1.0 + pred_returns)

        # Persistence Baseline: predicts price at t+h equals current price at t (0% return)
        pred_prices_baseline = test_current_price.values

        # Calculate metrics on actual price levels
        actual_prices = y_test_price.values

        xgb_mae = float(mean_absolute_error(actual_prices, pred_prices_xgb))
        xgb_rmse = float(np.sqrt(mean_squared_error(actual_prices, pred_prices_xgb)))
        xgb_r2 = float(r2_score(actual_prices, pred_prices_xgb))
        xgb_metrics = ForecastMetrics(mae=xgb_mae, rmse=xgb_rmse, r2=xgb_r2)

        base_mae = float(mean_absolute_error(actual_prices, pred_prices_baseline))
        base_rmse = float(np.sqrt(mean_squared_error(actual_prices, pred_prices_baseline)))
        base_r2 = float(r2_score(actual_prices, pred_prices_baseline))
        base_metrics = ForecastMetrics(mae=base_mae, rmse=base_rmse, r2=base_r2)

        outperformed = (xgb_mae < base_mae) or (xgb_rmse < base_rmse)

        # Store latest observation state for subsequent out-of-sample forecasting
        cleaned = clean_oil_price_data(df)
        series_clean = cleaned[cleaned["series"] == self.series].sort_values("period")
        self.last_observed_date = series_clean["period"].iloc[-1]
        self.last_observed_price = float(series_clean["value"].iloc[-1])

        return ModelComparisonResult(
            horizon_days=self.horizon_days,
            series=self.series,
            sample_count_train=len(train_idx_purged),
            sample_count_test=len(test_idx),
            train_end_date=train_end_date,
            test_start_date=test_start_date,
            test_end_date=test_end_date,
            xgboost_metrics=xgb_metrics,
            baseline_metrics=base_metrics,
            outperformed_baseline=outperformed,
        )

    def forecast(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates out-of-sample forecast for the next horizon using the latest observed features.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained yet. Call train_and_evaluate() first.")

        cleaned = clean_oil_price_data(df)
        series_df = cleaned[cleaned["series"] == self.series].sort_values("period").reset_index(drop=True)
        if series_df.empty:
            raise ValueError(f"No records found for series '{self.series}' to generate forecast.")

        feat_df = build_oil_features(series_df)
        latest_row = feat_df.iloc[-1:]

        # Validate that required features are present
        X_latest = latest_row[self.feature_cols]
        if X_latest.isna().any(axis=1).iloc[0]:
            raise ValueError("Latest observation contains NaN in feature columns; insufficient warm-up history.")

        X_latest_scaled = self.scaler.transform(X_latest)
        predicted_return = float(self.model.predict(X_latest_scaled)[0])

        current_price = float(latest_row["value"].iloc[0])
        current_date = pd.to_datetime(latest_row["period"].iloc[0])
        predicted_price = current_price * (1.0 + predicted_return)
        forecast_target_date = current_date + pd.Timedelta(days=self.horizon_days)

        return {
            "series": self.series,
            "horizon_days": self.horizon_days,
            "as_of_date": str(current_date.date()),
            "forecast_target_date": str(forecast_target_date.date()),
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "predicted_return_pct": round(predicted_return * 100.0, 2),
            "persistence_baseline_price": round(current_price, 2),
        }


class MultiHorizonOilForecaster:
    """
    Orchestrator for multi-horizon (7d, 30d, 90d) forecasting across Brent and WTI.
    """

    def __init__(self, horizons: Optional[List[int]] = None):
        self.horizons = horizons or SUPPORTED_HORIZONS
        self.forecasters: Dict[str, Dict[int, OilPriceForecaster]] = {
            "RBRTE": {},
            "RWTC": {},
        }

    def train_and_evaluate_all(
        self,
        df: pd.DataFrame,
        series_list: Optional[List[str]] = None,
        test_size: float = 0.2,
    ) -> Dict[str, Dict[int, ModelComparisonResult]]:
        """
        Trains and benchmarks all requested series across all horizons.
        """
        target_series = series_list or ["RBRTE", "RWTC"]
        results: Dict[str, Dict[int, ModelComparisonResult]] = {}

        for s in target_series:
            norm_s = SERIES_ALIASES.get(s.lower(), s.upper())
            results[norm_s] = {}
            for h in self.horizons:
                forecaster = OilPriceForecaster(series=norm_s, horizon_days=h)
                try:
                    eval_result = forecaster.train_and_evaluate(df, test_size=test_size)
                    self.forecasters[norm_s][h] = forecaster
                    results[norm_s][h] = eval_result
                except ValueError as e:
                    # Capture graceful error reporting for insufficient data per horizon
                    results[norm_s][h] = {"error": str(e), "horizon_days": h, "series": norm_s}

        return results

    def forecast_all(self, df: pd.DataFrame, series: str = "RBRTE") -> List[Dict[str, Any]]:
        """
        Returns forecasts for all trained horizons for a given series.
        """
        norm_s = SERIES_ALIASES.get(series.lower(), series.upper())
        if norm_s not in self.forecasters or not self.forecasters[norm_s]:
            raise RuntimeError(f"No trained forecasters found for series '{norm_s}'. Train first.")

        forecasts = []
        for h, forecaster in self.forecasters[norm_s].items():
            if forecaster.is_fitted:
                forecasts.append(forecaster.forecast(df))
        return forecasts
