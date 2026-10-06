"""
Configuration and constants for What-If Geopolitical Simulator (Member 3 Milestone 4).
Centralizes file paths, baseline selection rules, simulation defaults, and scenario archetypes.
"""

from pathlib import Path
from typing import Any, Dict, List

# Base directory resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Input baseline paths (Member 3 processed outputs)
PROCESSED_RELATIONSHIPS_DIR = DATA_DIR / "processed" / "relationships"
BASELINE_METRICS_PATH = PROCESSED_RELATIONSHIPS_DIR / "country_network_metrics.parquet"
BASELINE_DYADS_PATH = PROCESSED_RELATIONSHIPS_DIR / "country_dyad_relationships.parquet"

PROCESSED_NEWS_DIR = DATA_DIR / "processed" / "news"
BASELINE_NEWS_PATH = PROCESSED_NEWS_DIR / "country_month_news_features.parquet"

PROCESSED_UCDP_DIR = DATA_DIR / "processed" / "ucdp"
BASELINE_UCDP_PATH = PROCESSED_UCDP_DIR / "country_month_conflict_features.parquet"

# Output paths
PROCESSED_SCENARIOS_DIR = DATA_DIR / "processed" / "scenarios"
OUTPUT_COUNTRY_IMPACTS_PATH = PROCESSED_SCENARIOS_DIR / "scenario_country_impacts.parquet"
OUTPUT_DYAD_IMPACTS_PATH = PROCESSED_SCENARIOS_DIR / "scenario_dyad_impacts.parquet"
OUTPUT_GRAPH_JSON_PATH = PROCESSED_SCENARIOS_DIR / "scenario_graph.json"
OUTPUT_SUMMARY_JSON_PATH = PROCESSED_SCENARIOS_DIR / "simulation_summary.json"

# Baseline Selection Definition
# The empirical datasets have different historical/rolling coverages.
# This rule explicitly defines how the baseline t0 is selected without fabricating common dates:
BASELINE_NEWS_MONTH = "2026-09"       # Latest full calendar month with complete coverage (is_partial_month == False)
BASELINE_UCDP_MONTH = "2025-12"       # Latest available complete conflict observation month in UCDP GED 26.1
BASELINE_SELECTION_RULE = (
    "Anchored to the latest complete calendar month in the rolling GDELT news panel (2026-09, is_partial_month=False), "
    "combined with cumulative empirical relationship network topology (1989-2026) and latest complete UCDP conflict panel (2025-12)."
)

# Simulation Default Parameters
DEFAULT_PROPAGATION_DEPTH: int = 2
DEFAULT_DECAY_FACTOR: float = 0.5
MAX_PROPAGATION_DEPTH: int = 4

# Pre-defined Scenario Archetypes (transparent, analytical parameter templates)
SCENARIO_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "diplomatic_escalation": {
        "description": "Sharp deterioration in diplomatic relations and rhetoric.",
        "tone_delta": -0.4,
        "conflict_news_multiplier": 1.5,
        "decay_factor": 0.5,
        "propagation_depth": 2,
    },
    "sanctions_severance": {
        "description": "Economic sanctions and severance of diplomatic/economic ties.",
        "tone_delta": -0.3,
        "conflict_news_multiplier": 1.2,
        "sever_dyadic_tie": True,
        "decay_factor": 0.4,
        "propagation_depth": 2,
    },
    "military_mobilization": {
        "description": "Troop buildup and heightened military readiness.",
        "tone_delta": -0.6,
        "conflict_news_multiplier": 2.0,
        "decay_factor": 0.6,
        "propagation_depth": 2,
    },
    "ceasefire_deescalation": {
        "description": "Formal ceasefire agreement and commencement of peace negotiations.",
        "tone_delta": 0.5,
        "conflict_news_multiplier": 0.3,
        "decay_factor": 0.5,
        "propagation_depth": 2,
    },
}
