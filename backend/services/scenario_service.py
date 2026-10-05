from typing import Any, Dict
from fastapi import HTTPException

from backend.schemas.scenarios import ScenarioSimulationRequest
from backend.services.economic_service import economic_service
from backend.services.oil_service import oil_service
from ml.scenarios.what_if_engine import PRESET_SCENARIOS, WhatIfEngine


class ScenarioService:
    """
    Service layer running counterfactual What-If scenario simulations through actual trained models.
    """

    def __init__(self):
        self.engine = WhatIfEngine()

    def get_presets(self) -> Dict[str, str]:
        return PRESET_SCENARIOS

    def simulate(self, req: ScenarioSimulationRequest) -> Dict[str, Any]:
        target_type = req.target_type.lower()
        horizon = req.horizon_days
        scenario = req.scenario_name.lower()
        mods = req.modifications or {}

        try:
            if target_type == "oil":
                series = req.series or "RBRTE"
                forecaster, oil_df = oil_service.get_or_train_forecaster(series=series, horizon_days=horizon)
                result = self.engine.simulate_oil_scenario(
                    forecaster=forecaster,
                    df=oil_df,
                    scenario_name=scenario,
                    modifications=mods,
                )
                res = result.to_dict()
                res["changed_inputs"] = res.get("changed_input_features", {})
                res["limitations_notice"] = (
                    "Counterfactual scenario outputs represent model projections under hypothetical input shocks "
                    "and should not be interpreted as guaranteed outcomes."
                )
                return res

            elif target_type == "economic":
                country = req.country or "USA"
                forecaster, macro_df, oil_df = economic_service.get_or_train_forecaster(
                    country=country,
                    horizon_days=horizon,
                )
                result = self.engine.simulate_economic_scenario(
                    forecaster=forecaster,
                    macro_df=macro_df,
                    oil_df=oil_df,
                    scenario_name=scenario,
                    modifications=mods,
                )
                res = result.to_dict()
                res["changed_inputs"] = res.get("changed_input_features", {})
                res["limitations_notice"] = (
                    "Counterfactual scenario outputs represent model projections under hypothetical input shocks "
                    "and should not be interpreted as guaranteed outcomes."
                )
                return res

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported target_type '{target_type}'. Use 'oil' or 'economic'.")

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except TypeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


scenario_service = ScenarioService()
