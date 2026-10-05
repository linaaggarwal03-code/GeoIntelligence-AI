import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException
import pandas as pd

from backend.config import settings
from ml.data_ingestion.eia_fetcher import EIAFetcher
from ml.data_ingestion.http_client import APIKeyMissingError, APIResponseError
from ml.explainability.shap_explainer import ModelExplainer
from ml.models.oil_forecaster import (
    OilPriceForecaster,
    SERIES_ALIASES,
    SUPPORTED_HORIZONS,
)


class OilService:
    """
    Service layer orchestrating oil price ingestion, forecasting, evaluation, and SHAP explanations.
    """

    def __init__(self, raw_data_dir: Path = Path("data/raw/eia")):
        self.raw_data_dir = raw_data_dir
        self.fetcher = EIAFetcher(raw_data_dir=raw_data_dir)
        # Cache trained forecasters: key = (normalized_series, horizon_days)
        self._forecaster_cache: Dict[Tuple[str, int], OilPriceForecaster] = {}
        # In-memory dataframe cache for oil observations
        self._data_cache: Dict[str, pd.DataFrame] = {}

    def normalize_series(self, series: str) -> str:
        s = series.strip().lower()
        normalized = SERIES_ALIASES.get(s, s.upper())
        if normalized not in ["RBRTE", "RWTC"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported oil series '{series}'. Allowed values: 'brent', 'wti', 'RBRTE', 'RWTC'.",
            )
        return normalized

    def validate_horizon(self, horizon_days: int) -> int:
        if horizon_days not in SUPPORTED_HORIZONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported horizon {horizon_days}d. Allowed horizons: {SUPPORTED_HORIZONS}.",
            )
        return horizon_days

    def load_or_fetch_oil_data(self, series: str) -> pd.DataFrame:
        """
        Loads cached oil data or invokes EIAFetcher.
        If EIA_API_KEY is not configured and no local data exists, raises 503 HTTP error.
        """
        normalized = self.normalize_series(series)
        if normalized in self._data_cache:
            return self._data_cache[normalized]

        try:
            df = self.fetcher.fetch_oil_spot_prices(series=normalized, frequency="daily")
            if not df.empty:
                self._data_cache[normalized] = df
                return df
        except APIKeyMissingError as e:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"EIA API Key is not configured. Set EIA_API_KEY in the environment or .env file to enable live oil data. "
                    f"Details: {str(e)}"
                ),
            )
        except APIResponseError as e:
            raise HTTPException(
                status_code=502,
                detail=f"EIA external API returned an error: {str(e)}",
            )

        raise HTTPException(
            status_code=404,
            detail=f"No oil price observations found for series '{normalized}'.",
        )

    def set_in_memory_data(self, series: str, df: pd.DataFrame) -> None:
        """Helper to inject datasets for testing or offline mode."""
        normalized = self.normalize_series(series)
        self._data_cache[normalized] = df

    def get_or_train_forecaster(self, series: str, horizon_days: int) -> Tuple[OilPriceForecaster, pd.DataFrame]:
        normalized = self.normalize_series(series)
        horizon = self.validate_horizon(horizon_days)

        cache_key = (normalized, horizon)
        oil_df = self.load_or_fetch_oil_data(normalized)

        if cache_key in self._forecaster_cache:
            return self._forecaster_cache[cache_key], oil_df

        forecaster = OilPriceForecaster(series=normalized, horizon_days=horizon)
        try:
            forecaster.train_and_evaluate(oil_df)
            self._forecaster_cache[cache_key] = forecaster
            return forecaster, oil_df
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_forecast(self, series: str, horizon_days: int) -> Dict[str, Any]:
        forecaster, oil_df = self.get_or_train_forecaster(series, horizon_days)
        try:
            return forecaster.forecast(oil_df)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

    def get_evaluation(self, series: str, horizon_days: int) -> Dict[str, Any]:
        forecaster, oil_df = self.get_or_train_forecaster(series, horizon_days)
        eval_res = forecaster.train_and_evaluate(oil_df)
        return eval_res.to_dict()

    def get_explanation(self, series: str, horizon_days: int, mode: str = "local") -> Dict[str, Any]:
        forecaster, oil_df = self.get_or_train_forecaster(series, horizon_days)
        explainer = ModelExplainer(forecaster)

        feat_df = forecaster._prepare_features_and_targets(oil_df)[0]
        X_feats = feat_df[forecaster.feature_cols]

        if mode.lower() == "global":
            explanation = explainer.explain_global(X_feats.tail(100), top_n=10)
        elif mode.lower() == "local":
            latest_instance = X_feats.iloc[[-1]]
            explanation = explainer.explain_local(latest_instance, top_n=8)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported explanation mode '{mode}'. Use 'local' or 'global'.")

        return {
            "series": forecaster.series,
            "horizon_days": forecaster.horizon_days,
            "mode": mode.lower(),
            "explanation": explanation.to_dict(),
        }


oil_service = OilService()
