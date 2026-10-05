from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException
import pandas as pd

from backend.services.oil_service import oil_service
from ml.data_ingestion.http_client import APIResponseError
from ml.data_ingestion.worldbank_fetcher import DEFAULT_ECONOMIC_INDICATORS, WorldBankFetcher
from ml.explainability.shap_explainer import ModelExplainer
from ml.models.economic_impact import (
    EconomicImpactForecaster,
    SUPPORTED_ECONOMIC_HORIZONS,
)


class EconomicService:
    """
    Service layer orchestrating World Bank macroeconomic data ingestion,
    mixed-frequency alignment with oil signals, impact forecasting, evaluation, and SHAP explanations.
    """

    def __init__(self, raw_data_dir: Path = Path("data/raw/worldbank")):
        self.raw_data_dir = raw_data_dir
        self.fetcher = WorldBankFetcher(raw_data_dir=raw_data_dir)
        self._macro_cache: Dict[str, pd.DataFrame] = {}
        self._forecaster_cache: Dict[Tuple[str, str, int], EconomicImpactForecaster] = {}

    def validate_horizon(self, horizon_days: int) -> int:
        if horizon_days not in SUPPORTED_ECONOMIC_HORIZONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported horizon {horizon_days}d. Allowed horizons: {SUPPORTED_ECONOMIC_HORIZONS}.",
            )
        return horizon_days

    def load_or_fetch_macro_data(self, country: str) -> pd.DataFrame:
        c_code = country.strip().upper()
        if c_code in self._macro_cache:
            return self._macro_cache[c_code]

        # Ingest core macroeconomic indicators for the country
        indicators = list(DEFAULT_ECONOMIC_INDICATORS.values())
        try:
            df = self.fetcher.fetch_multiple_indicators(indicators=indicators, countries=[c_code])
            if not df.empty:
                self._macro_cache[c_code] = df
                return df
        except APIResponseError as e:
            raise HTTPException(
                status_code=502,
                detail=f"World Bank API error: {str(e)}",
            )

        raise HTTPException(
            status_code=404,
            detail=f"No macroeconomic observations found for country '{c_code}'.",
        )

    def set_in_memory_data(self, country: str, df: pd.DataFrame) -> None:
        """Inject test or offline datasets directly into service."""
        c_code = country.strip().upper()
        self._macro_cache[c_code] = df

    def get_or_train_forecaster(
        self,
        country: str,
        horizon_days: int,
        target_indicator: str = "inflation_impact_pct",
        model_type: str = "xgboost",
    ) -> Tuple[EconomicImpactForecaster, pd.DataFrame, pd.DataFrame]:
        c_code = country.strip().upper()
        horizon = self.validate_horizon(horizon_days)

        cache_key = (c_code, target_indicator, horizon)
        macro_df = self.load_or_fetch_macro_data(c_code)
        # Pull Brent oil data as global energy signal
        oil_df = oil_service.load_or_fetch_oil_data(series="RBRTE")

        if cache_key in self._forecaster_cache:
            return self._forecaster_cache[cache_key], macro_df, oil_df

        forecaster = EconomicImpactForecaster(
            country=c_code,
            target_indicator=target_indicator,
            horizon_days=horizon,
            model_type=model_type,
        )
        try:
            forecaster.train_and_evaluate(macro_df=macro_df, oil_df=oil_df)
            self._forecaster_cache[cache_key] = forecaster
            return forecaster, macro_df, oil_df
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_forecast(
        self,
        country: str,
        horizon_days: int,
        target_indicator: str = "inflation_impact_pct",
    ) -> Dict[str, Any]:
        forecaster, macro_df, oil_df = self.get_or_train_forecaster(country, horizon_days, target_indicator)
        try:
            return forecaster.forecast_impact(macro_df=macro_df, oil_df=oil_df)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate economic impact forecast: {str(e)}")

    def get_evaluation(
        self,
        country: str,
        horizon_days: int,
        target_indicator: str = "inflation_impact_pct",
    ) -> Dict[str, Any]:
        forecaster, macro_df, oil_df = self.get_or_train_forecaster(country, horizon_days, target_indicator)
        eval_res = forecaster.train_and_evaluate(macro_df=macro_df, oil_df=oil_df)
        return eval_res.to_dict()

    def get_explanation(
        self,
        country: str,
        horizon_days: int,
        target_indicator: str = "inflation_impact_pct",
        mode: str = "local",
    ) -> Dict[str, Any]:
        forecaster, macro_df, oil_df = self.get_or_train_forecaster(country, horizon_days, target_indicator)
        explainer = ModelExplainer(forecaster)

        aligned_df = forecaster.build_mixed_frequency_dataset(macro_df, oil_df)
        X_all, _ = forecaster._generate_target(aligned_df)
        X_feats = X_all[forecaster.feature_cols]

        if mode.lower() == "global":
            explanation = explainer.explain_global(X_feats.tail(100), top_n=10)
        elif mode.lower() == "local":
            latest_instance = X_feats.iloc[[-1]]
            explanation = explainer.explain_local(latest_instance, top_n=8)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported explanation mode '{mode}'. Use 'local' or 'global'.")

        return {
            "country": forecaster.country,
            "target_indicator": forecaster.target_indicator,
            "horizon_days": forecaster.horizon_days,
            "mode": mode.lower(),
            "explanation": explanation.to_dict(),
        }


economic_service = EconomicService()
