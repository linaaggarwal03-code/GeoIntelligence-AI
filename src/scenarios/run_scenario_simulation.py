"""
CLI Orchestrator for What-If Geopolitical Simulator (Member 3 Milestone 4).
Runs deterministic scenario simulations, validates outputs, and exports Parquet and JSON artifacts.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.scenarios.config import (
    PROCESSED_SCENARIOS_DIR,
    OUTPUT_COUNTRY_IMPACTS_PATH,
    OUTPUT_DYAD_IMPACTS_PATH,
    OUTPUT_GRAPH_JSON_PATH,
    OUTPUT_SUMMARY_JSON_PATH,
)
from src.scenarios.engine import ScenarioEngine
from src.scenarios.schema import ScenarioDefinition, SimulationResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scenario_runner")


def validate_simulation_outputs(result: SimulationResult) -> None:
    """
    Validate counterfactual simulation outputs against data integrity and safety constraints.
    """
    logger.info("Validating counterfactual simulation outputs...")

    df_countries = pd.DataFrame(result.country_impacts)
    df_dyads = pd.DataFrame(result.dyad_impacts)

    # 1. 125 Reference countries present
    assert len(df_countries) == 125, f"Expected 125 countries, got {len(df_countries)}"

    # 2. PageRank sum conservation
    pr_sum = df_countries["counterfactual_pagerank"].sum()
    assert abs(pr_sum - 1.0) < 1e-3, f"Counterfactual PageRank sum {pr_sum} does not equal 1.0!"

    # 3. Tone bounds [-1.0, 1.0]
    tones = df_countries["counterfactual_tone"]
    assert (tones >= -1.0).all() and (tones <= 1.0).all(), (
        f"Counterfactual tone out of bounds [-1, 1]: min={tones.min()}, max={tones.max()}"
    )

    # 4. Tension bounds [0.0, 1.0]
    tensions = df_dyads["counterfactual_tension_index"]
    assert (tensions >= 0.0).all() and (tensions <= 1.0).all(), (
        f"Counterfactual tension out of bounds [0, 1]: min={tensions.min()}, max={tensions.max()}"
    )

    # 5. Non-negative degrees
    assert (df_countries["counterfactual_in_degree"] >= 0).all()
    assert (df_countries["counterfactual_out_degree"] >= 0).all()
    assert (df_countries["counterfactual_total_degree"] >= 0).all()

    # 6. Graph JSON format
    assert "nodes" in result.graph_json and "links" in result.graph_json
    assert len(result.graph_json["nodes"]) == 125
    assert len(result.graph_json["links"]) == len(df_dyads)

    logger.info("Output validation PASSED successfully.")


def run_simulation(
    scenario: Optional[ScenarioDefinition] = None,
    output_dir: Optional[Path] = None,
) -> SimulationResult:
    """
    Execute simulation and write output artifacts to disk.
    """
    out_dir = output_dir or PROCESSED_SCENARIOS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = ScenarioEngine()

    # Default illustrative scenario if none provided:
    # Middle East diplomatic escalation between Iran and Israel
    if scenario is None:
        scenario = ScenarioDefinition(
            scenario_id="scenario_mideast_diplomatic_shock",
            name="Middle East Diplomatic Escalation & Sanctions Shock",
            description="Simulates acute diplomatic deterioration and negative tone shock for Iran with bilateral tension escalation toward Israel.",
            target_country_iso3="IRN",
            target_dyad=("IRN", "ISR"),
            archetype="diplomatic_escalation",
            tone_delta=-0.4,
            conflict_news_multiplier=1.8,
            tension_delta=0.2,
            propagation_depth=2,
            decay_factor=0.5,
        )

    result = engine.simulate(scenario)

    # Save country impacts
    df_countries = pd.DataFrame(result.country_impacts)
    df_countries.to_parquet(
        OUTPUT_COUNTRY_IMPACTS_PATH, index=False, engine="pyarrow", compression="snappy"
    )
    logger.info("Saved scenario country impacts to: %s", OUTPUT_COUNTRY_IMPACTS_PATH)

    # Save dyad impacts
    df_dyads = pd.DataFrame(result.dyad_impacts)
    df_dyads.to_parquet(
        OUTPUT_DYAD_IMPACTS_PATH, index=False, engine="pyarrow", compression="snappy"
    )
    logger.info("Saved scenario dyad impacts to: %s", OUTPUT_DYAD_IMPACTS_PATH)

    # Save scenario graph JSON
    with open(OUTPUT_GRAPH_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result.graph_json, f, indent=2)
    logger.info("Saved scenario graph JSON to: %s", OUTPUT_GRAPH_JSON_PATH)

    # Save simulation summary
    with open(OUTPUT_SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result.summary, f, indent=2)
    logger.info("Saved simulation summary JSON to: %s", OUTPUT_SUMMARY_JSON_PATH)

    # Validation
    validate_simulation_outputs(result)

    logger.info(
        "=== Simulation Completed: %s (Target: %s, Affected Countries: %d) ===",
        scenario.name,
        scenario.target_country_iso3,
        result.summary["simulation_statistics"]["total_affected_countries_count"],
    )

    return result


if __name__ == "__main__":
    run_simulation()
