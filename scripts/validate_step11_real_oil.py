import json
from pathlib import Path
import sys

# Ensure repository root is in Python module search path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import Any, Dict, List
import pandas as pd

from ml.data_ingestion.eia_fetcher import EIAFetcher
from ml.data_ingestion.worldbank_fetcher import WorldBankFetcher
from ml.features.oil_features import build_oil_features, clean_oil_price_data
from ml.models.oil_forecaster import OilPriceForecaster, SUPPORTED_HORIZONS
from ml.models.economic_impact import EconomicImpactForecaster
from ml.explainability.shap_explainer import ModelExplainer
from ml.scenarios.what_if_engine import WhatIfEngine


def run_step11_validation() -> Dict[str, Any]:
    print("=" * 70)
    print("STEP 11: REAL PRODUCTION OIL FORECAST & ECONOMIC VALIDATION")
    print("=" * 70)

    # 1. Fetch Real Brent and WTI Data from EIA v2 API
    print("\n[1/6] Fetching genuine Brent & WTI daily data via EIA API...")
    fetcher = EIAFetcher(raw_data_dir=Path("data/raw/eia"))
    brent_raw = fetcher.fetch_oil_spot_prices(series="RBRTE", frequency="daily", start_date="2015-01-01", save_raw=True)
    wti_raw = fetcher.fetch_oil_spot_prices(series="RWTC", frequency="daily", start_date="2015-01-01", save_raw=True)

    brent_summary = {
        "series": "Brent (RBRTE)",
        "observations": len(brent_raw),
        "start_date": str(brent_raw["period"].min().date()),
        "end_date": str(brent_raw["period"].max().date()),
        "min_price": round(float(brent_raw["value"].min()), 2),
        "max_price": round(float(brent_raw["value"].max()), 2),
        "latest_price": round(float(brent_raw["value"].iloc[-1]), 2),
    }

    wti_summary = {
        "series": "WTI (RWTC)",
        "observations": len(wti_raw),
        "start_date": str(wti_raw["period"].min().date()),
        "end_date": str(wti_raw["period"].max().date()),
        "min_price": round(float(wti_raw["value"].min()), 2),
        "max_price": round(float(wti_raw["value"].max()), 2),
        "latest_price": round(float(wti_raw["value"].iloc[-1]), 2),
    }

    print(f"  Brent: {brent_summary['observations']} obs ({brent_summary['start_date']} to {brent_summary['end_date']}), latest: ${brent_summary['latest_price']}")
    print(f"  WTI:   {wti_summary['observations']} obs ({wti_summary['start_date']} to {wti_summary['end_date']}), latest: ${wti_summary['latest_price']}")

    # 2. Build Feature Sets from Real Data
    print("\n[2/6] Building time-series feature engineering matrices...")
    brent_feats = build_oil_features(brent_raw)
    wti_feats = build_oil_features(wti_raw)
    feature_columns = [c for c in brent_feats.columns if c not in ["period", "series", "value", "source", "units", "series_description"]]
    print(f"  Constructed {len(feature_columns)} engineered features per series across {len(brent_feats)} Brent and {len(wti_feats)} WTI records.")

    # 3. Train & Evaluate Models across Horizons (7d, 30d, 90d)
    print("\n[3/6] Training & evaluating multi-horizon forecasting pipelines...")
    oil_results = {}
    trained_forecasters = {}

    for series_name, raw_df in [("Brent", brent_raw), ("WTI", wti_raw)]:
        oil_results[series_name] = {}
        for h in SUPPORTED_HORIZONS:
            series_code = "RBRTE" if series_name == "Brent" else "RWTC"
            forecaster = OilPriceForecaster(series=series_code, horizon_days=h)
            eval_metrics = forecaster.train_and_evaluate(raw_df, test_size=0.20)
            forecast_out = forecaster.forecast(raw_df)

            key = f"{h}d"
            oil_results[series_name][key] = {
                "horizon_days": h,
                "evaluation": eval_metrics.to_dict(),
                "forecast": forecast_out,
            }
            trained_forecasters[(series_code, h)] = forecaster

            print(f"  [{series_name} {h:2d}d] Out-of-sample Test: {eval_metrics.test_start_date} to {eval_metrics.test_end_date} ({eval_metrics.sample_count_test} obs)")
            print(f"         XGBoost:  MAE=${eval_metrics.xgboost_metrics.mae:.2f} | RMSE=${eval_metrics.xgboost_metrics.rmse:.2f} | R2={eval_metrics.xgboost_metrics.r2:.4f}")
            print(f"         Baseline: MAE=${eval_metrics.baseline_metrics.mae:.2f} | RMSE=${eval_metrics.baseline_metrics.rmse:.2f} | R2={eval_metrics.baseline_metrics.r2:.4f}")
            print(f"         Outperform Baseline? {eval_metrics.outperformed_baseline}")
            print(f"         Forecast: Current=${forecast_out['current_price']:.2f} -> Target ({forecast_out['forecast_target_date']})=${forecast_out['predicted_price']:.2f} ({forecast_out['predicted_return_pct']:+.2f}%)")

    # 4. SHAP Explainability on Trained 30-Day Brent Model
    print("\n[4/6] Generating SHAP explainability matrices for 30-day Brent model...")
    brent_30d_forecaster = trained_forecasters[("RBRTE", 30)]
    explainer = ModelExplainer(brent_30d_forecaster)
    brent_eval_test_size = oil_results["Brent"]["30d"]["evaluation"]["test_samples"]
    global_shap = explainer.explain_global(brent_feats.iloc[-brent_eval_test_size:])

    latest_brent_feat_row = brent_feats.iloc[-1:]
    local_shap = explainer.explain_local(latest_brent_feat_row)

    shap_results = {
        "model": "Brent 30-day XGBoost",
        "base_value": global_shap.base_value,
        "sample_count": global_shap.sample_count,
        "top_global_features": [f.to_dict() for f in global_shap.feature_importances[:8]],
        "local_explanation": {
            "base_value": local_shap.base_value,
            "predicted_return": local_shap.prediction_value,
            "top_positive_drivers": [d.to_dict() for d in local_shap.top_positive_drivers[:4]],
            "top_negative_drivers": [d.to_dict() for d in local_shap.top_negative_drivers[:4]],
        }
    }
    print(f"  SHAP Base Expected Return: {global_shap.base_value:+.4f}")
    print("  Top 5 Global Predictive Drivers:")
    for feat in global_shap.feature_importances[:5]:
        print(f"    - #{feat.rank} {feat.feature:<25} (Mean |SHAP| = {feat.mean_abs_shap:.6f})")

    # 5. What-If Scenario Simulations on Real Feature Vector
    print("\n[5/6] Executing What-If Counterfactual Stress Tests...")
    scenario_engine = WhatIfEngine()
    pos_shock_res = scenario_engine.simulate_oil_scenario(
        forecaster=brent_30d_forecaster,
        df=brent_raw,
        scenario_name="positive_oil_shock",
    )
    neg_shock_res = scenario_engine.simulate_oil_scenario(
        forecaster=brent_30d_forecaster,
        df=brent_raw,
        scenario_name="negative_oil_shock",
    )

    scenario_results = {
        "positive_oil_shock": pos_shock_res.to_dict(),
        "negative_oil_shock": neg_shock_res.to_dict(),
    }
    print(f"  Positive Shock (+25% price, +50% vol):")
    print(f"    Baseline 30d: ${pos_shock_res.baseline_forecast:.2f} -> Scenario: ${pos_shock_res.scenario_forecast:.2f} (Diff: ${pos_shock_res.absolute_difference:+.2f} / {pos_shock_res.percentage_difference:+.2f}%)")
    print(f"  Negative Shock (-25% price, +25% vol):")
    print(f"    Baseline 30d: ${neg_shock_res.baseline_forecast:.2f} -> Scenario: ${neg_shock_res.scenario_forecast:.2f} (Diff: ${neg_shock_res.absolute_difference:+.2f} / {neg_shock_res.percentage_difference:+.2f}%)")

    # 6. Economic Impact Forecasting on Real Macro + Oil Features
    print("\n[6/6] Executing Mixed-Frequency Economic Impact Validation...")
    wb_fetcher = WorldBankFetcher()
    macro_dfs = []
    for json_file in Path("data/raw/worldbank").glob("USA_*.json"):
        with open(json_file, "r") as f:
            raw_json = json.load(f)
        if isinstance(raw_json, list) and len(raw_json) > 1:
            ind_code = json_file.stem.replace("USA_", "")
            macro_dfs.append(wb_fetcher._to_dataframe(raw_json[1], indicator=ind_code))

    if not macro_dfs:
        print("  [WARNING] No local World Bank data found. Attempting live fetch...")
        combined_macro = wb_fetcher.fetch_multiple_indicators(
            indicators=["NY.GDP.MKTP.CD", "FP.CPI.TOTL.ZG", "NE.EXP.GNFS.ZS", "NE.IMP.GNFS.ZS"],
            countries=["USA"],
            start_year=2000,
            end_year=2024,
        )
    else:
        combined_macro = pd.concat(macro_dfs, ignore_index=True)

    econ_forecaster = EconomicImpactForecaster(
        country="USA",
        target_indicator="inflation_impact_pct",
        horizon_days=30,
        model_type="xgboost",
    )
    econ_eval = econ_forecaster.train_and_evaluate(macro_df=combined_macro, oil_df=brent_raw)
    econ_forecast = econ_forecaster.forecast_impact(macro_df=combined_macro, oil_df=brent_raw)

    aligned_econ = econ_forecaster.build_mixed_frequency_dataset(macro_df=combined_macro, oil_df=brent_raw)
    X_econ_all, _ = econ_forecaster._generate_target(aligned_econ)
    econ_explainer = ModelExplainer(econ_forecaster)
    econ_global_shap = econ_explainer.explain_global(X_econ_all[econ_forecaster.feature_cols].iloc[-econ_eval.sample_count_test:])

    economic_results = {
        "country": "USA",
        "target_indicator": "inflation_impact_pct",
        "horizon_days": 30,
        "evaluation": econ_eval.to_dict(),
        "forecast": econ_forecast,
        "top_features": [f.to_dict() for f in econ_global_shap.feature_importances[:5]],
    }
    print(f"  USA Inflation Impact (30-day horizon):", flush=True)
    print(f"    Train: {econ_eval.sample_count_train} samples ({econ_eval.train_end_period}) | Test: {econ_eval.sample_count_test} samples ({econ_eval.test_start_period} to {econ_eval.test_end_period})", flush=True)
    print(f"    ML Model: MAE={econ_eval.ml_metrics.mae:.4f} | RMSE={econ_eval.ml_metrics.rmse:.4f} | R2={econ_eval.ml_metrics.r2:.4f}", flush=True)
    print(f"    Baseline: MAE={econ_eval.baseline_metrics.mae:.4f} | RMSE={econ_eval.baseline_metrics.rmse:.4f} | R2={econ_eval.baseline_metrics.r2:.4f}", flush=True)
    print(f"    Outperformed Baseline: {econ_eval.outperformed_baseline}", flush=True)
    print(f"    Projected Inflation Impact: {econ_forecast['predicted_impact_value']:+.4f}% (Baseline ref: {econ_forecast['baseline_reference_value']:+.4f}%)", flush=True)

    validation_payload = {
        "brent_summary": brent_summary,
        "wti_summary": wti_summary,
        "oil_multi_horizon_results": oil_results,
        "shap_results": shap_results,
        "scenario_results": scenario_results,
        "economic_results": economic_results,
    }

    # Save to scratch directory
    scratch_dir = Path("data/processed")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    out_file = scratch_dir / "step11_real_validation_summary.json"
    with open(out_file, "w") as f:
        json.dump(validation_payload, f, indent=2)
    print(f"\n[OK] Validation complete! Saved detailed metrics to {out_file}")

    return validation_payload


if __name__ == "__main__":
    run_step11_validation()
