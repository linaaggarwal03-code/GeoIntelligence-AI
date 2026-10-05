from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from ml.features.economic_features import build_economic_panel, engineer_economic_features
from ml.features.oil_features import build_oil_features, clean_oil_price_data
from ml.features.shipping_features import extract_trade_concentration_features


SUPPORTED_ECONOMIC_HORIZONS: List[int] = [7, 30, 90]


@dataclass
class EconomicImpactMetrics:
    """Evaluation metrics for economic impact forecasting."""
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
class EconomicModelComparisonResult:
    """Holds comparative evaluation between ML model and baseline."""
    country: str
    target_indicator: str
    horizon_days: int
    model_type: str
    sample_count_train: int
    sample_count_test: int
    train_end_period: str
    test_start_period: str
    test_end_period: str
    ml_metrics: EconomicImpactMetrics
    baseline_metrics: EconomicImpactMetrics
    outperformed_baseline: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country,
            "target_indicator": self.target_indicator,
            "horizon_days": self.horizon_days,
            "model_type": self.model_type,
            "train_samples": self.sample_count_train,
            "test_samples": self.sample_count_test,
            "train_end_period": self.train_end_period,
            "test_start_period": self.test_start_period,
            "test_end_period": self.test_end_period,
            "ml_model": self.ml_metrics.to_dict(),
            "baseline": self.baseline_metrics.to_dict(),
            "outperformed_baseline": self.outperformed_baseline,
        }


class EconomicImpactForecaster:
    """
    Mixed-frequency Economic Impact Forecaster for geopolitical and energy shocks.

    Key Econometric & Architectural Design:
    1. Mixed-Frequency Alignment:
       - Macroeconomic indicators (World Bank: GDP, inflation, trade openness) are annual.
         They are never artificially interpolated into daily numbers.
       - High-frequency commodity signals (oil price returns, rolling volatility, momentum)
         and trade concentration (HHI) are aligned with the macroeconomic state
         at the valid evaluation dates, respecting publication lags (reporting lag >= 1 year).
    2. Transmission Mechanics:
       - Interacts global energy shock magnitude (oil return/volatility) with country-specific
         structural vulnerability (trade openness %, import dependency %, partner concentration).
    3. Temporal Validation:
       - Strictly chronological train/test split.
       - No future lookahead; scalers and estimators fit strictly on historical data.
    4. Benchmarking:
       - Compares against historical persistence / mean baseline.
    """

    def __init__(
        self,
        country: str = "WLD",
        target_indicator: str = "inflation_impact_pct",
        horizon_days: int = 30,
        model_type: str = "xgboost",  # 'xgboost' or 'random_forest'
        n_estimators: int = 100,
        max_depth: int = 4,
        random_state: int = 42,
    ):
        if horizon_days not in SUPPORTED_ECONOMIC_HORIZONS:
            raise ValueError(f"Unsupported horizon {horizon_days}. Expected one of {SUPPORTED_ECONOMIC_HORIZONS} days.")

        self.country = country.upper().strip()
        self.target_indicator = target_indicator
        self.horizon_days = horizon_days
        self.model_type = model_type.lower()
        self.random_state = random_state

        if self.model_type == "xgboost":
            self.model = XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=0.05,
                subsample=0.85,
                random_state=random_state,
                n_jobs=-1,
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unsupported model_type '{model_type}'. Expected 'xgboost' or 'random_forest'.")

        self.scaler = StandardScaler()
        self.feature_cols: List[str] = []
        self.is_fitted = False
        self.baseline_historical_mean: float = 0.0

    def build_mixed_frequency_dataset(
        self,
        macro_df: pd.DataFrame,
        oil_df: pd.DataFrame,
        trade_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Combines annual country macro features with trailing high-frequency oil/trade features.
        Preserves strict temporal integrity with a 1-year publication lag on macro fundamentals.
        """
        # 1. Process Macro Panel
        panel = build_economic_panel(macro_df, impute_strategy="forward_fill", forward_fill_limit=2)
        panel_feats = engineer_economic_features(panel)
        country_macro = panel_feats[panel_feats["country_iso3"] == self.country].copy()

        if country_macro.empty:
            raise ValueError(f"No macroeconomic records found for country '{self.country}'.")

        # 2. Process High-Frequency Oil Features
        oil_feats = build_oil_features(oil_df)
        if oil_feats.empty:
            raise ValueError("No oil feature records provided.")

        oil_feats["period"] = pd.to_datetime(oil_feats["period"])
        oil_feats = oil_feats.sort_values("period").reset_index(drop=True)

        # 3. Process Trade Concentration (if provided)
        trade_hhi = {}
        if trade_df is not None and not trade_df.empty:
            hhi_df = extract_trade_concentration_features(trade_df)
            if not hhi_df.empty:
                c_hhi = hhi_df[hhi_df["reporter_iso"] == self.country]
                for _, row in c_hhi.iterrows():
                    trade_hhi[str(row["period"])] = float(row["hhi_concentration"])

        # 4. Mixed-Frequency Alignment:
        # For each oil date t, match with known macroeconomic fundamentals from year (year(t) - 1)
        # to strictly respect annual data reporting delays.
        records = []
        macro_years = sorted(country_macro["year"].unique())

        for idx, row in oil_feats.iterrows():
            current_date = row["period"]
            # Available published macro year is strictly prior to current year
            avail_years = [y for y in macro_years if y < current_date.year]
            if not avail_years:
                continue
            latest_macro_year = avail_years[-1]
            macro_row = country_macro[country_macro["year"] == latest_macro_year].iloc[0]

            record = {
                "period": current_date,
                "country_iso3": self.country,
                "macro_reporting_year": latest_macro_year,
                # Macro fundamentals
                "gdp_growth_pct": macro_row.get("gdp_growth_pct", np.nan),
                "inflation_pct": macro_row.get("inflation_pct", np.nan),
                "trade_openness_pct_gdp": macro_row.get("trade_openness_pct_gdp", np.nan),
                "trade_balance_pct_gdp": macro_row.get("trade_balance_pct_gdp", np.nan),
                "log_gdp": macro_row.get("log_gdp", np.nan),
                # Oil signals
                "oil_price": row["value"],
                "oil_return_1d": row.get("return_1d", 0.0),
                "oil_return_5d": row.get("return_5d", 0.0),
                "oil_return_20d": row.get("return_20d", 0.0),
                "oil_volatility_30d": row.get("rolling_volatility_30d", 0.0),
                "oil_price_to_ma_30d": row.get("price_to_ma_30d", 0.0),
                # Trade concentration
                "trade_hhi": trade_hhi.get(str(latest_macro_year), 0.15),
            }

            # Economic Transmission Interaction Features:
            # Impact of energy moves scales with trade openness and net trade balance
            trade_open = record["trade_openness_pct_gdp"] if not np.isnan(record["trade_openness_pct_gdp"]) else 50.0
            trade_bal = record["trade_balance_pct_gdp"] if not np.isnan(record["trade_balance_pct_gdp"]) else 0.0

            # Transmission feature: Oil Return Shock * Trade Openness
            record["energy_shock_exposure"] = (record["oil_return_20d"] * (trade_open / 100.0))
            # Vulnerability feature: Oil Volatility * Partner Concentration
            record["supply_chain_vulnerability"] = (record["oil_volatility_30d"] * record["trade_hhi"])

            records.append(record)

        df_aligned = pd.DataFrame(records)
        return df_aligned.sort_values("period").reset_index(drop=True)

    def _generate_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Derives target economic pressure/impact variable over the specified horizon.
        Default target: forward inflation impact pressure from cumulative energy & trade shocks.
        """
        data = df.copy()

        # Target over horizon h: forward cumulative energy price pressure interacting with inflation baseline
        # Forward oil return over horizon_days: (P_{t+h} - P_t) / P_t
        future_oil_price = data["oil_price"].shift(-self.horizon_days)
        forward_oil_return = (future_oil_price - data["oil_price"]) / data["oil_price"]

        if self.target_indicator == "inflation_impact_pct":
            # Economic transmission equation:
            # Forward inflation impact = Base inflation * 0.10 + (forward oil return * energy exposure elasticity)
            base_inflation = data["inflation_pct"].fillna(2.5)
            openness_ratio = (data["trade_openness_pct_gdp"].fillna(50.0) / 100.0)
            target = (forward_oil_return * openness_ratio * 10.0) + (base_inflation * (self.horizon_days / 365.0))
        elif self.target_indicator == "gdp_growth_impact_pct":
            # Forward GDP growth drag from energy volatility and price shocks
            base_growth = data["gdp_growth_pct"].fillna(2.0)
            target = base_growth - (np.abs(forward_oil_return) * 2.5)
        else:
            # Custom column or direct forward calculation
            if self.target_indicator in data.columns:
                target = data[self.target_indicator].shift(-self.horizon_days)
            else:
                target = forward_oil_return * 100.0

        target.name = self.target_indicator

        exclude_cols = [
            "period", "country_iso3", "macro_reporting_year"
        ]
        feature_cols = [c for c in data.columns if c not in exclude_cols]

        # Valid rows where target is not NaN (drop last horizon_days)
        valid_idx = target.dropna().index
        clean_X = data.loc[valid_idx, feature_cols].copy()
        clean_y = target.loc[valid_idx]

        # Explicit missing value handling in features
        for col in clean_X.columns:
            if clean_X[col].isna().any():
                clean_X[f"{col}_missing"] = clean_X[col].isna().astype(float)
                clean_X[col] = clean_X[col].fillna(clean_X[col].median() if not np.isnan(clean_X[col].median()) else 0.0)

        clean_X.insert(0, "_period", data.loc[valid_idx, "period"])
        return clean_X, clean_y

    def train_and_evaluate(
        self,
        macro_df: pd.DataFrame,
        oil_df: pd.DataFrame,
        trade_df: Optional[pd.DataFrame] = None,
        test_size: float = 0.2,
    ) -> EconomicModelComparisonResult:
        """
        Executes chronological train/test split, trains ML model, and benchmarks against persistence.
        """
        aligned_df = self.build_mixed_frequency_dataset(macro_df, oil_df, trade_df)
        X_all, y_all = self._generate_target(aligned_df)

        n_samples = len(X_all)
        min_required = 40 + self.horizon_days
        if n_samples < min_required:
            raise ValueError(
                f"Insufficient historical aligned samples for country '{self.country}' at horizon {self.horizon_days}d. "
                f"Found {n_samples}, required minimum {min_required}."
            )

        n_test = max(10, int(np.floor(n_samples * test_size)))
        n_train = n_samples - n_test

        train_idx = np.arange(0, n_train)
        test_idx = np.arange(n_train, n_samples)

        # Purging gap to prevent overlap
        purge_gap = max(0, min(self.horizon_days, int(n_train * 0.15)))
        train_idx_purged = train_idx[:-purge_gap] if purge_gap > 0 else train_idx

        feature_cols = [c for c in X_all.columns if c != "_period"]
        self.feature_cols = feature_cols

        X_train_raw = X_all.iloc[train_idx_purged][feature_cols]
        y_train = y_all.iloc[train_idx_purged]

        X_test_raw = X_all.iloc[test_idx][feature_cols]
        y_test = y_all.iloc[test_idx]

        train_end_period = str(X_all.iloc[train_idx_purged]["_period"].max().date())
        test_start_period = str(X_all.iloc[test_idx]["_period"].min().date())
        test_end_period = str(X_all.iloc[test_idx]["_period"].max().date())

        # Fit Scaler strictly on train
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_test_scaled = self.scaler.transform(X_test_raw)

        # Fit ML Model
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True

        # ML Predictions
        pred_ml = self.model.predict(X_test_scaled)

        # Baseline: Historical Training Mean / Persistence
        self.baseline_historical_mean = float(y_train.mean())
        pred_baseline = np.full_like(y_test, fill_value=self.baseline_historical_mean)

        actual = y_test.values

        ml_mae = float(mean_absolute_error(actual, pred_ml))
        ml_rmse = float(np.sqrt(mean_squared_error(actual, pred_ml)))
        ml_r2 = float(r2_score(actual, pred_ml))
        ml_metrics = EconomicImpactMetrics(mae=ml_mae, rmse=ml_rmse, r2=ml_r2)

        base_mae = float(mean_absolute_error(actual, pred_baseline))
        base_rmse = float(np.sqrt(mean_squared_error(actual, pred_baseline)))
        base_r2 = float(r2_score(actual, pred_baseline))
        base_metrics = EconomicImpactMetrics(mae=base_mae, rmse=base_rmse, r2=base_r2)

        outperformed = (ml_mae < base_mae) or (ml_rmse < base_rmse)

        return EconomicModelComparisonResult(
            country=self.country,
            target_indicator=self.target_indicator,
            horizon_days=self.horizon_days,
            model_type=self.model_type,
            sample_count_train=len(train_idx_purged),
            sample_count_test=len(test_idx),
            train_end_period=train_end_period,
            test_start_period=test_start_period,
            test_end_period=test_end_period,
            ml_metrics=ml_metrics,
            baseline_metrics=base_metrics,
            outperformed_baseline=outperformed,
        )

    def forecast_impact(
        self,
        macro_df: pd.DataFrame,
        oil_df: pd.DataFrame,
        trade_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Generates out-of-sample forward economic impact forecast from the latest observed state.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained yet. Call train_and_evaluate() first.")

        aligned_df = self.build_mixed_frequency_dataset(macro_df, oil_df, trade_df)
        if aligned_df.empty:
            raise ValueError(f"Cannot generate impact forecast: no aligned data for country '{self.country}'.")

        latest_row = aligned_df.iloc[-1:]
        current_date = pd.to_datetime(latest_row["period"].iloc[0])
        target_date = current_date + pd.Timedelta(days=self.horizon_days)

        # Build feature vector
        X_latest = pd.DataFrame()
        for col in self.feature_cols:
            if col in latest_row.columns:
                X_latest[col] = latest_row[col].values
            else:
                X_latest[col] = 0.0

        X_latest_scaled = self.scaler.transform(X_latest)
        predicted_impact = float(self.model.predict(X_latest_scaled)[0])

        return {
            "country": self.country,
            "target_indicator": self.target_indicator,
            "horizon_days": self.horizon_days,
            "as_of_date": str(current_date.date()),
            "forecast_target_date": str(target_date.date()),
            "macro_reporting_year": int(latest_row["macro_reporting_year"].iloc[0]),
            "predicted_impact_value": round(predicted_impact, 4),
            "baseline_reference_value": round(self.baseline_historical_mean, 4),
            "model_type": self.model_type,
        }
