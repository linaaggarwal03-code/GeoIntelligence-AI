"""
End-to-End Orchestrator for Country Relationship Network Pipeline (Member 3 Milestone 3).
Executes bilateral UCDP state dyad extraction, directed GDELT news dyad aggregation,
topological graph centrality calculation, and generates Parquet and JSON artifacts with metadata.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.relationships.config import (
    UCDP_EVENTS_PATH,
    UCDP_FEATURES_PATH,
    NEWS_ARTICLES_PATH,
    PROCESSED_RELATIONSHIPS_DIR,
    OUTPUT_DYADS_PATH,
    OUTPUT_METRICS_PATH,
    OUTPUT_GRAPH_JSON_PATH,
    OUTPUT_METADATA_PATH,
)
from src.relationships.dyad_extractor import (
    extract_ucdp_bilateral_dyads,
    aggregate_cumulative_dyads,
    build_monthly_dyads_panel,
)
from src.relationships.graph_builder import (
    compute_node_network_metrics,
    build_network_graph_json,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("relationship_pipeline")


def validate_outputs(
    dyads_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    graph_json: Dict[str, Any],
    reference_countries: List[str],
) -> None:
    """
    Validate relationship network outputs against data integrity and schema requirements.
    """
    logger.info("Running comprehensive output validation...")

    # 1. Dyad table validation
    required_dyad_cols = [
        "source_country_iso3",
        "target_country_iso3",
        "period_type",
        "has_historical_conflict",
        "conflict_events_total",
        "fatalities_best_total",
        "news_article_count",
        "composite_tension_index",
    ]
    for col in required_dyad_cols:
        assert col in dyads_df.columns, f"Missing required column in dyads table: {col}"

    # Verify no source == target self-loops
    assert not (dyads_df["source_country_iso3"] == dyads_df["target_country_iso3"]).any(), (
        "Dyad table contains forbidden self-loops (source == target)!"
    )

    # Verify composite tension index bounds [0.0, 1.0]
    tension = dyads_df["composite_tension_index"]
    assert (tension >= 0.0).all() and (tension <= 1.0).all(), (
        f"Composite tension index out of bounds [0.0, 1.0]: min={tension.min()}, max={tension.max()}"
    )

    # 2. Node metrics validation
    assert len(metrics_df) == len(reference_countries), (
        f"Node metrics count ({len(metrics_df)}) does not match reference country count ({len(reference_countries)})!"
    )
    assert set(metrics_df["country_iso3"]) == set(reference_countries), (
        "Node metrics countries do not perfectly match the 125 reference countries!"
    )

    # Verify PageRank sum == 1.0 within numerical tolerance
    pr_sum = metrics_df["pagerank_centrality"].sum()
    assert abs(pr_sum - 1.0) < 1e-3, f"PageRank sum {pr_sum} does not equal 1.0!"

    # Verify in/out degree non-negative integers
    assert (metrics_df["in_degree"] >= 0).all()
    assert (metrics_df["out_degree"] >= 0).all()

    # 3. Graph JSON validation
    assert "nodes" in graph_json and "links" in graph_json, "Graph JSON missing 'nodes' or 'links'!"
    assert len(graph_json["nodes"]) == len(reference_countries), "Graph JSON nodes count mismatch!"
    assert len(graph_json["links"]) == len(dyads_df), "Graph JSON links count mismatch with dyad table!"

    logger.info("Output validation PASSED successfully.")


def run_relationship_pipeline(
    ucdp_events_path: Optional[Path] = None,
    news_articles_path: Optional[Path] = None,
    reference_features_path: Optional[Path] = None,
) -> None:
    """
    Run complete Country Relationship Network pipeline.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("=== STEP 1: Loading Processed Datasets ===")

    u_events_path = ucdp_events_path or UCDP_EVENTS_PATH
    n_articles_path = news_articles_path or NEWS_ARTICLES_PATH
    ref_path = reference_features_path or UCDP_FEATURES_PATH

    if not u_events_path.exists():
        raise FileNotFoundError(f"Clean UCDP events file not found at: {u_events_path}")
    if not n_articles_path.exists():
        raise FileNotFoundError(f"Clean news articles file not found at: {n_articles_path}")
    if not ref_path.exists():
        raise FileNotFoundError(f"Reference UCDP features file not found at: {ref_path}")

    logger.info("Loading UCDP clean events from %s...", u_events_path)
    ucdp_events_df = pd.read_parquet(u_events_path)
    logger.info("Loaded %d UCDP event records.", len(ucdp_events_df))

    logger.info("Loading cleaned news articles from %s...", n_articles_path)
    news_df = pd.read_parquet(n_articles_path)
    logger.info("Loaded %d cleaned news article records.", len(news_df))

    logger.info("Loading reference country universe from %s...", ref_path)
    ref_df = pd.read_parquet(ref_path, columns=["country_iso3"])
    reference_countries = sorted(ref_df["country_iso3"].unique().tolist())
    logger.info("Resolved %d standard reference countries.", len(reference_countries))

    logger.info("=== STEP 2: Extracting Bilateral State UCDP Dyads ===")
    bilateral_events_df, exclusion_stats = extract_ucdp_bilateral_dyads(ucdp_events_df)

    logger.info("=== STEP 3: Aggregating Cumulative Dyadic Relationships ===")
    cumulative_dyads_df = aggregate_cumulative_dyads(
        ucdp_events_df=bilateral_events_df,
        news_df=news_df,
    )
    logger.info(
        "Extracted %d unique directed dyadic links (top tension: %s -> %s, tension=%.2f).",
        len(cumulative_dyads_df),
        cumulative_dyads_df.iloc[0]["source_country_iso3"] if not cumulative_dyads_df.empty else "N/A",
        cumulative_dyads_df.iloc[0]["target_country_iso3"] if not cumulative_dyads_df.empty else "N/A",
        cumulative_dyads_df.iloc[0]["composite_tension_index"] if not cumulative_dyads_df.empty else 0.0,
    )

    logger.info("=== STEP 4: Computing Country-Level Topological Network Metrics ===")
    node_metrics_df = compute_node_network_metrics(
        reference_countries=reference_countries,
        dyads_df=cumulative_dyads_df,
        weight_col="composite_tension_index",
    )
    logger.info(
        "Top country by PageRank centrality: %s (PR=%.4f, total_degree=%d).",
        node_metrics_df.iloc[0]["country_iso3"],
        node_metrics_df.iloc[0]["pagerank_centrality"],
        node_metrics_df.iloc[0]["total_degree"],
    )

    logger.info("=== STEP 5: Serializing Decoupled Graph JSON ===")
    graph_json = build_network_graph_json(
        nodes_df=node_metrics_df,
        dyads_df=cumulative_dyads_df,
    )

    logger.info("=== STEP 6: Saving Outputs ===")
    PROCESSED_RELATIONSHIPS_DIR.mkdir(parents=True, exist_ok=True)

    cumulative_dyads_df.to_parquet(
        OUTPUT_DYADS_PATH, index=False, engine="pyarrow", compression="snappy"
    )
    logger.info("Saved dyad relationships table to: %s", OUTPUT_DYADS_PATH)

    node_metrics_df.to_parquet(
        OUTPUT_METRICS_PATH, index=False, engine="pyarrow", compression="snappy"
    )
    logger.info("Saved country network metrics table to: %s", OUTPUT_METRICS_PATH)

    with open(OUTPUT_GRAPH_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(graph_json, f, indent=2)
    logger.info("Saved network graph JSON to: %s", OUTPUT_GRAPH_JSON_PATH)

    # Run validations
    validate_outputs(
        dyads_df=cumulative_dyads_df,
        metrics_df=node_metrics_df,
        graph_json=graph_json,
        reference_countries=reference_countries,
    )

    logger.info("=== STEP 7: Writing Processing Metadata ===")
    duration_sec = (datetime.now(timezone.utc) - start_time).total_seconds()
    conflict_dyads_count = int(cumulative_dyads_df["has_historical_conflict"].sum())
    news_dyads_count = int((cumulative_dyads_df["news_article_count"] > 0).sum())

    metadata = {
        "dataset_name": "Country Relationship Network & Graph Metrics",
        "pipeline_version": "1.0.0",
        "created_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_sources": {
            "ucdp_events_file": str(u_events_path.name),
            "news_articles_file": str(n_articles_path.name),
            "reference_panel_file": str(ref_path.name),
        },
        "output_files": {
            "dyads_parquet": str(OUTPUT_DYADS_PATH.name),
            "metrics_parquet": str(OUTPUT_METRICS_PATH.name),
            "network_graph_json": str(OUTPUT_GRAPH_JSON_PATH.name),
        },
        "input_statistics": {
            "raw_ucdp_events_count": len(ucdp_events_df),
            "raw_news_articles_count": len(news_df),
            "reference_countries_count": len(reference_countries),
        },
        "ucdp_dyad_exclusion_statistics": exclusion_stats,
        "graph_statistics": {
            "total_reference_nodes": len(reference_countries),
            "active_nodes_with_edges": int(node_metrics_df["has_active_edges"].sum()),
            "total_directed_dyads": len(cumulative_dyads_df),
            "bilateral_conflict_dyads": conflict_dyads_count,
            "directed_news_dyads": news_dyads_count,
            "max_tension_index": float(cumulative_dyads_df["composite_tension_index"].max())
            if not cumulative_dyads_df.empty
            else 0.0,
        },
        "forecasting_safety": {
            "temporal_leakage_prevented": True,
            "prior_only_lags_enforced": True,
            "unavailable_history_preserved_as_nan": True,
            "zero_news_preserved_only_within_observed_window": True,
        },
        "composite_tension_definition": {
            "analytical_formula": "0.6 * S_conflict + 0.4 * S_news",
            "conflict_scaling": "min(1.0, ln(1 + fatalities) / ln(1 + 1000.0))",
            "news_scaling": "0.5 * max(0, -avg_tone) + 0.5 * conflict_news_share",
            "notes": "Analytical project-derived indicator; not an official UCDP/GDELT definition.",
        },
        "pipeline_duration_seconds": round(duration_sec, 2),
    }

    with open(OUTPUT_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Saved processing metadata to: %s", OUTPUT_METADATA_PATH)

    logger.info(
        "=== Country Relationship Network Pipeline Completed in %.1f seconds ===", duration_sec
    )


if __name__ == "__main__":
    run_relationship_pipeline()
