from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ml.features.oil_features import build_oil_features, clean_oil_price_data
from ml.models.economic_impact import EconomicImpactForecaster
from ml.models.oil_forecaster import OilPriceForecaster


PRESET_SCENARIOS = {
    "baseline": "No modifications to existing historical inputs.",
    "positive_oil_shock": "Sudden upward energy shock (+25% return, +50% volatility) simulating geopolitical supply disruptions.",
    "negative_oil_shock": "Sudden downward energy shock (-25% return, +25% volatility) simulating demand contraction or oversupply.",
    "supply_chain_crisis": "High maritime chokepoint concentration (+50% HHI) combined with elevated oil volatility.",
}


@dataclass
class ScenarioResult:
    """Standardized output structure for What-If scenario simulations."""
    scenario_name: str
    target_type: str  # 'oil_price' or 'economic_impact'
    horizon_days: int
    baseline_forecast: float
    scenario_forecast: float
    absolute_difference: float
    percentage_difference: float
    changed_input_features: Dict[str, Dict[str, float]]
    as_of_date: str
    forecast_target_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "target_type": self.target_type,
            "horizon_days": int(self.horizon_days),
            "baseline_forecast": round(float(self.baseline_forecast), 4),
            "scenario_forecast": round(float(self.scenario_forecast), 4),
            "absolute_difference": round(float(self.absolute_difference), 4),
            "percentage_difference": round(float(self.percentage_difference), 4),
            "changed_input_features": self.changed_input_features,
            "as_of_date": self.as_of_date,
            "forecast_target_date": self.forecast_target_date,
        }


class WhatIfEngine:
    """
    Simulation engine for stress-testing and counterfactual analysis.

    Enables geopolitical intelligence analysts to simulate:
    - Oil supply shocks (+/- percentage price and return shifts)
    - Volatility spikes (annualized rolling standard deviation shocks)
    - Trade openness and partner concentration shifts (HHI disruptions)

    Strict Architecture:
    - All scenario outputs originate directly from actual trained models.
    - No hardcoded forecast percentages or synthetic predictions.
    - Inputs are rigorously validated (no negative prices, HHI bounded [0, 1]).
    - Deterministic: identical inputs and scenario modifications yield identical results.
    """

    def __init__(self):
        pass

    def _validate_modifications(
        self,
        modifications: Dict[str, Any],
        allowed_features: List[str],
        additional_params: Optional[List[str]] = None,
    ) -> None:
        """
        Validates modification keys and ensures values are finite, numeric, and bounded.
        """
        permitted = set(allowed_features) | set(additional_params or [])

        for key, val in modifications.items():
            if key not in permitted:
                raise ValueError(
                    f"Unknown scenario feature: '{key}'. Permitted features for this model: {sorted(list(permitted))}"
                )

            if not isinstance(val, (int, float, np.number)):
                raise TypeError(f"Scenario value for '{key}' must be numeric, got {type(val)}: {val}")

            if np.isnan(val) or np.isinf(val):
                raise ValueError(f"Scenario value for '{key}' cannot be NaN or infinite.")

            # Bounded domain checks
            if key in ["oil_price", "current_price", "value"] and val <= 0:
                raise ValueError(f"Oil price must be strictly positive, got {val}.")
            if key in ["trade_hhi", "hhi_concentration"] and not (0.0 <= val <= 1.0):
                raise ValueError(f"Trade concentration (HHI) must be in [0.0, 1.0], got {val}.")
            if "volatility" in key and val < 0:
                raise ValueError(f"Volatility feature '{key}' cannot be negative, got {val}.")
            if "trade_openness" in key and val < 0:
                raise ValueError(f"Trade openness '{key}' cannot be negative, got {val}.")

    def simulate_oil_scenario(
        self,
        forecaster: OilPriceForecaster,
        df: pd.DataFrame,
        scenario_name: str = "baseline",
        modifications: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResult:
        """
        Simulates an oil price scenario through a trained OilPriceForecaster.

        :param forecaster: Fitted OilPriceForecaster instance.
        :param df: Historical oil observations DataFrame.
        :param scenario_name: 'baseline', 'positive_oil_shock', 'negative_oil_shock', or 'custom'.
        :param modifications: Dictionary of specific feature perturbations or overrides.
        """
        if not forecaster.is_fitted:
            raise RuntimeError("OilPriceForecaster must be fitted before running scenarios.")

        cleaned = clean_oil_price_data(df)
        series_df = cleaned[cleaned["series"] == forecaster.series].sort_values("period").reset_index(drop=True)
        if series_df.empty:
            raise ValueError(f"No records found for series '{forecaster.series}'.")

        # 1. Baseline Run
        feat_df = build_oil_features(series_df)
        latest_row = feat_df.iloc[-1:].copy()
        current_price = float(latest_row["value"].iloc[0])
        as_of_date = pd.to_datetime(latest_row["period"].iloc[0])
        target_date = as_of_date + pd.Timedelta(days=forecaster.horizon_days)

        X_base = latest_row[forecaster.feature_cols].copy()
        X_base_scaled = forecaster.scaler.transform(X_base)
        base_pred_return = float(forecaster.model.predict(X_base_scaled)[0])
        base_pred_price = current_price * (1.0 + base_pred_return)

        # 2. Configure Scenario Modifications
        applied_mods: Dict[str, Any] = {}
        target_price = current_price

        if scenario_name == "positive_oil_shock":
            applied_mods = {
                "return_1d": float(latest_row.get("return_1d", 0.0).iloc[0]) + 0.05,
                "return_5d": float(latest_row.get("return_5d", 0.0).iloc[0]) + 0.15,
                "return_20d": float(latest_row.get("return_20d", 0.0).iloc[0]) + 0.25,
                "rolling_volatility_30d": float(latest_row.get("rolling_volatility_30d", 0.2).iloc[0]) * 1.5,
                "price_to_ma_30d": float(latest_row.get("price_to_ma_30d", 0.0).iloc[0]) + 0.15,
            }
            target_price = current_price * 1.10
        elif scenario_name == "negative_oil_shock":
            applied_mods = {
                "return_1d": float(latest_row.get("return_1d", 0.0).iloc[0]) - 0.05,
                "return_5d": float(latest_row.get("return_5d", 0.0).iloc[0]) - 0.15,
                "return_20d": float(latest_row.get("return_20d", 0.0).iloc[0]) - 0.25,
                "rolling_volatility_30d": float(latest_row.get("rolling_volatility_30d", 0.2).iloc[0]) * 1.25,
                "price_to_ma_30d": float(latest_row.get("price_to_ma_30d", 0.0).iloc[0]) - 0.15,
            }
            target_price = current_price * 0.90
        elif scenario_name == "baseline":
            applied_mods = {}
        elif scenario_name == "custom":
            applied_mods = modifications or {}
        else:
            raise ValueError(
                f"Unsupported scenario_name '{scenario_name}'. Expected 'baseline', 'positive_oil_shock', 'negative_oil_shock', or 'custom'."
            )

        # Merge custom modifications if provided on top of presets
        if scenario_name != "custom" and modifications:
            applied_mods.update(modifications)

        # Validate modifications
        additional_params = ["oil_price", "current_price"]
        self._validate_modifications(applied_mods, forecaster.feature_cols, additional_params)

        if "oil_price" in applied_mods:
            target_price = float(applied_mods["oil_price"])
        elif "current_price" in applied_mods:
            target_price = float(applied_mods["current_price"])

        # 3. Apply Modifications to Feature Vector
        X_scenario = X_base.copy()
        changed_features: Dict[str, Dict[str, float]] = {}

        for col, new_val in applied_mods.items():
            if col in forecaster.feature_cols:
                old_val = float(X_base[col].iloc[0])
                X_scenario[col] = float(new_val)
                changed_features[col] = {
                    "baseline": round(old_val, 4),
                    "scenario": round(float(new_val), 4),
                    "delta": round(float(new_val) - old_val, 4),
                }

        if target_price != current_price:
            changed_features["current_price"] = {
                "baseline": round(current_price, 2),
                "scenario": round(target_price, 2),
                "delta": round(target_price - current_price, 2),
            }

        # 4. Predict Scenario through Trained Model
        X_scen_scaled = forecaster.scaler.transform(X_scenario)
        scen_pred_return = float(forecaster.model.predict(X_scen_scaled)[0])
        scen_pred_price = target_price * (1.0 + scen_pred_return)

        abs_diff = scen_pred_price - base_pred_price
        pct_diff = (abs_diff / base_pred_price * 100.0) if base_pred_price != 0 else 0.0

        return ScenarioResult(
            scenario_name=scenario_name,
            target_type="oil_price",
            horizon_days=forecaster.horizon_days,
            baseline_forecast=base_pred_price,
            scenario_forecast=scen_pred_price,
            absolute_difference=abs_diff,
            percentage_difference=pct_diff,
            changed_input_features=changed_features,
            as_of_date=str(as_of_date.date()),
            forecast_target_date=str(target_date.date()),
        )

    def simulate_economic_scenario(
        self,
        forecaster: EconomicImpactForecaster,
        macro_df: pd.DataFrame,
        oil_df: pd.DataFrame,
        trade_df: Optional[pd.DataFrame] = None,
        scenario_name: str = "baseline",
        modifications: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResult:
        """
        Simulates an economic impact scenario through a trained EconomicImpactForecaster.
        """
        if not forecaster.is_fitted:
            raise RuntimeError("EconomicImpactForecaster must be fitted before running scenarios.")

        aligned_df = forecaster.build_mixed_frequency_dataset(macro_df, oil_df, trade_df)
        if aligned_df.empty:
            raise ValueError(f"No aligned data available for country '{forecaster.country}'.")

        latest_row = aligned_df.iloc[-1:].copy()
        as_of_date = pd.to_datetime(latest_row["period"].iloc[0])
        target_date = as_of_date + pd.Timedelta(days=forecaster.horizon_days)

        # Baseline prediction
        X_base = pd.DataFrame()
        for col in forecaster.feature_cols:
            if col in latest_row.columns:
                X_base[col] = latest_row[col].values
            else:
                X_base[col] = 0.0

        X_base_scaled = forecaster.scaler.transform(X_base)
        base_impact = float(forecaster.model.predict(X_base_scaled)[0])

        # Configure Scenario
        applied_mods: Dict[str, Any] = {}
        if scenario_name == "positive_oil_shock":
            applied_mods = {
                "oil_return_20d": float(latest_row.get("oil_return_20d", 0.0).iloc[0]) + 0.30,
                "oil_volatility_30d": float(latest_row.get("oil_volatility_30d", 0.25).iloc[0]) * 1.5,
            }
        elif scenario_name == "negative_oil_shock":
            applied_mods = {
                "oil_return_20d": float(latest_row.get("oil_return_20d", 0.0).iloc[0]) - 0.30,
                "oil_volatility_30d": float(latest_row.get("oil_volatility_30d", 0.25).iloc[0]) * 1.25,
            }
        elif scenario_name == "supply_chain_crisis":
            applied_mods = {
                "trade_hhi": min(1.0, float(latest_row.get("trade_hhi", 0.2).iloc[0]) + 0.35),
                "oil_volatility_30d": float(latest_row.get("oil_volatility_30d", 0.25).iloc[0]) * 1.75,
            }
        elif scenario_name == "baseline":
            applied_mods = {}
        elif scenario_name == "custom":
            applied_mods = modifications or {}
        else:
            raise ValueError(
                f"Unsupported scenario_name '{scenario_name}'. Expected 'baseline', 'positive_oil_shock', 'negative_oil_shock', 'supply_chain_crisis', or 'custom'."
            )

        if scenario_name != "custom" and modifications:
            applied_mods.update(modifications)

        self._validate_modifications(applied_mods, forecaster.feature_cols)

        # Apply perturbations
        X_scenario = X_base.copy()
        changed_features: Dict[str, Dict[str, float]] = {}

        for col, new_val in applied_mods.items():
            if col in forecaster.feature_cols:
                old_val = float(X_base[col].iloc[0])
                X_scenario[col] = float(new_val)
                changed_features[col] = {
                    "baseline": round(old_val, 4),
                    "scenario": round(float(new_val), 4),
                    "delta": round(float(new_val) - old_val, 4),
                }

        # Update interaction terms if key drivers changed
        if "energy_shock_exposure" in forecaster.feature_cols and "oil_return_20d" in applied_mods:
            openness = float(X_scenario["trade_openness_pct_gdp"].iloc[0]) if "trade_openness_pct_gdp" in X_scenario else 50.0
            new_exposure = float(X_scenario["oil_return_20d"].iloc[0]) * (openness / 100.0)
            X_scenario["energy_shock_exposure"] = new_exposure

        if "supply_chain_vulnerability" in forecaster.feature_cols and ("oil_volatility_30d" in applied_mods or "trade_hhi" in applied_mods):
            vol = float(X_scenario["oil_volatility_30d"].iloc[0]) if "oil_volatility_30d" in X_scenario else 0.25
            hhi = float(X_scenario["trade_hhi"].iloc[0]) if "trade_hhi" in X_scenario else 0.2
            X_scenario["supply_chain_vulnerability"] = vol * hhi

        # Predict scenario through model
        X_scen_scaled = forecaster.scaler.transform(X_scenario)
        scen_impact = float(forecaster.model.predict(X_scen_scaled)[0])

        abs_diff = scen_impact - base_impact
        pct_diff = (abs_diff / abs(base_impact) * 100.0) if base_impact != 0 else 0.0

        return ScenarioResult(
            scenario_name=scenario_name,
            target_type="economic_impact",
            horizon_days=forecaster.horizon_days,
            baseline_forecast=base_impact,
            scenario_forecast=scen_impact,
            absolute_difference=abs_diff,
            percentage_difference=pct_diff,
            changed_input_features=changed_features,
            as_of_date=str(as_of_date.date()),
            forecast_target_date=str(target_date.date()),
        )
