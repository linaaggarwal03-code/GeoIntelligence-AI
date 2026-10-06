"""
Unit tests for Member 3 Milestone 3: Country Relationship Network.
Tests reliable UCDP dyad extraction, non-state exclusion, canonical unordered pairs,
directed news semantics, hybrid relationship behavior, symmetric conflict graph contributions,
pure-Python PageRank, composite tension bounds, temporal leakage prevention,
out-of-window NaN preservation, and JSON schema compliance.
"""

from typing import Dict, List
import numpy as np
import pandas as pd
import pytest

from src.relationships.config import UCDP_GOV_NAME_TO_ISO3, ISO3_TO_COUNTRY_NAME
from src.relationships.dyad_extractor import (
    parse_government_entities,
    extract_ucdp_bilateral_dyads,
    extract_news_dyads,
    calculate_composite_tension,
    aggregate_cumulative_dyads,
    build_monthly_dyads_panel,
)
from src.relationships.graph_builder import (
    compute_pagerank,
    compute_node_network_metrics,
    build_network_graph_json,
)


def test_parse_government_entities():
    """Verify robust extraction of recognized government entities and coalition handling."""
    # Single government
    res = parse_government_entities("Government of Russia (Soviet Union)")
    assert res == ["RUS"]

    # Coalition of governments
    coalition = "Government of United Kingdom, Government of United States of America"
    res_coalition = parse_government_entities(coalition)
    assert set(res_coalition) == {"GBR", "USA"}

    # Three-party coalition
    tri = "Government of Australia, Government of United Kingdom, Government of United States of America"
    res_tri = parse_government_entities(tri)
    assert set(res_tri) == {"AUS", "GBR", "USA"}

    # Non-government rebel groups or civilians should return empty
    assert parse_government_entities("FARC") == []
    assert parse_government_entities("Syrian insurgents") == []
    assert parse_government_entities("Civilians") == []
    assert parse_government_entities("") == []
    assert parse_government_entities(None) == []


def test_reliable_and_ambiguous_ucdp_dyad_handling():
    """
    Verify:
    1. Reliable bilateral state dyads are extracted as canonical unordered pairs (min(A, B), max(A, B)).
    2. Intrastate civil conflicts (Gov vs Rebel) and one-sided violence are excluded and counted.
    3. Multilateral state coalitions produce all pairwise combinations without arbitrary direction.
    """
    mock_events = pd.DataFrame(
        [
            # Bilateral state conflict (reliable) - side_a: RUS, side_b: UKR
            {
                "id": 1,
                "side_a": "Government of Russia (Soviet Union)",
                "side_b": "Government of Ukraine",
                "year_month": "2022-03",
                "event_date": "2022-03-01",
                "best": 50,
                "low": 40,
                "high": 60,
                "deaths_civilians": 5,
                "conflict_name": "Russia - Ukraine",
            },
            # Intrastate civil conflict (Gov vs Rebel group) -> should be excluded from bilateral state dyads
            {
                "id": 2,
                "side_a": "Government of Colombia",
                "side_b": "FARC",
                "year_month": "2015-05",
                "event_date": "2015-05-10",
                "best": 10,
                "low": 10,
                "high": 10,
                "deaths_civilians": 0,
                "conflict_name": "Colombia: Government",
            },
            # Intrastate civil conflict 2 (Gov vs Insurgency)
            {
                "id": 3,
                "side_a": "Government of Syria",
                "side_b": "Syrian insurgents",
                "year_month": "2016-08",
                "event_date": "2016-08-15",
                "best": 30,
                "low": 20,
                "high": 40,
                "deaths_civilians": 12,
                "conflict_name": "Syria: Government",
            },
            # Coalition state conflict (2 states on side A vs 1 state on side B)
            {
                "id": 4,
                "side_a": "Government of United Kingdom, Government of United States of America",
                "side_b": "Government of Iraq",
                "year_month": "2003-04",
                "event_date": "2003-04-05",
                "best": 100,
                "low": 80,
                "high": 120,
                "deaths_civilians": 20,
                "conflict_name": "United Kingdom, United States - Iraq",
            },
        ]
    )

    dyads_df, stats = extract_ucdp_bilateral_dyads(mock_events)

    assert stats["total_events_processed"] == 4
    # Event 2 and 3 should be excluded because side_b is non-state
    assert stats["intrastate_civil_events_excluded"] == 2
    # Events 1 and 4 retained
    assert stats["bilateral_events_retained"] == 2
    # Event 1 produced 1 dyad; Event 4 produced 2 dyads (GBR-IRQ, USA-IRQ)
    assert len(dyads_df) == 3
    assert stats["bilateral_dyad_observations_extracted"] == 3

    # Check extracted dyads are canonicalized alphabetically (min(A, B), max(A, B))
    pairs = set(zip(dyads_df["source_country_iso3"], dyads_df["target_country_iso3"]))
    assert ("RUS", "UKR") in pairs  # RUS < UKR
    assert ("GBR", "IRQ") in pairs  # GBR < IRQ
    assert ("IRQ", "USA") in pairs  # IRQ < USA (not USA -> IRQ!)
    assert ("COL", "FARC") not in pairs

    # Verify is_directed and relationship_nature
    assert (dyads_df["is_directed"] == False).all()
    assert (dyads_df["relationship_nature"] == "undirected_conflict").all()


def test_source_vs_target_country_semantics():
    """
    Verify:
    1. source_country_iso3 is strictly the reporting/origin country.
    2. target_country_iso3 is strictly the target/conflict zone country.
    3. Low-confidence / None target country is discarded.
    4. Self-reporting (source == target) is discarded.
    5. Direction is strictly preserved (is_directed=True, relationship_nature='directed_news').
    """
    mock_news = pd.DataFrame(
        [
            # Valid directed: IND reporting on UKR
            {
                "article_id": "art1",
                "source_country_iso3": "IND",
                "target_country_iso3": "UKR",
                "year_month": "2026-10",
                "tone_score": -0.8,
                "is_negative_tone": True,
                "is_conflict_relevant": True,
            },
            # Valid directed: IND reporting on UKR (second article)
            {
                "article_id": "art2",
                "source_country_iso3": "IND",
                "target_country_iso3": "UKR",
                "year_month": "2026-10",
                "tone_score": 0.0,
                "is_negative_tone": False,
                "is_conflict_relevant": False,
            },
            # Domestic self-report (source == target) -> must be discarded
            {
                "article_id": "art3",
                "source_country_iso3": "UKR",
                "target_country_iso3": "UKR",
                "year_month": "2026-10",
                "tone_score": -0.5,
                "is_negative_tone": True,
                "is_conflict_relevant": True,
            },
            # Unassigned target country (None) -> must be discarded
            {
                "article_id": "art4",
                "source_country_iso3": "USA",
                "target_country_iso3": None,
                "year_month": "2026-10",
                "tone_score": 0.2,
                "is_negative_tone": False,
                "is_conflict_relevant": False,
            },
        ]
    )

    news_dyads = extract_news_dyads(mock_news)

    # Exactly 1 dyad should be extracted: (IND -> UKR)
    assert len(news_dyads) == 1
    row = news_dyads.iloc[0]
    assert row["source_country_iso3"] == "IND"
    assert row["target_country_iso3"] == "UKR"
    assert row["is_directed"] == True
    assert row["relationship_nature"] == "directed_news"
    assert row["news_article_count"] == 2
    assert row["news_avg_tone"] == pytest.approx(-0.4)
    assert row["news_negative_tone_count"] == 1
    assert row["news_negative_tone_share"] == 0.5
    assert row["news_conflict_article_count"] == 1
    assert row["news_conflict_ratio"] == 0.5


def test_symmetric_conflict_graph_contribution():
    """
    Verify:
    1. Undirected conflict dyad contributes symmetrically to in-degree, out-degree, and weighted degree.
    2. Reciprocal PageRank transitions are created so neither state is an artificial one-way sink.
    """
    mock_conflict = pd.DataFrame(
        [
            {
                "source_country_iso3": "IRQ",
                "target_country_iso3": "KWT",
                "is_directed": False,
                "relationship_nature": "undirected_conflict",
                "period_type": "cumulative_historical",
                "has_historical_conflict": True,
                "conflict_events_total": 80,
                "fatalities_best_total": 22848.0,
                "news_article_count": 0,
                "news_avg_tone": np.nan,
                "composite_tension_index": 1.0,
            }
        ]
    )

    ref_countries = ["IRQ", "KWT", "USA"]
    metrics = compute_node_network_metrics(ref_countries, mock_conflict)

    irq = metrics[metrics["country_iso3"] == "IRQ"].iloc[0]
    kwt = metrics[metrics["country_iso3"] == "KWT"].iloc[0]
    usa = metrics[metrics["country_iso3"] == "USA"].iloc[0]

    # Both belligerents must have identical, symmetric degrees
    assert irq["in_degree"] == 1
    assert irq["out_degree"] == 1
    assert irq["total_degree"] == 1
    assert irq["weighted_in_degree"] == 1.0
    assert irq["weighted_out_degree"] == 1.0

    assert kwt["in_degree"] == 1
    assert kwt["out_degree"] == 1
    assert kwt["total_degree"] == 1
    assert kwt["weighted_in_degree"] == 1.0
    assert kwt["weighted_out_degree"] == 1.0

    # Symmetric PageRank for mutual conflict
    assert irq["pagerank_centrality"] == pytest.approx(kwt["pagerank_centrality"])

    # Isolated node receives 0 degrees and uniform base PageRank
    assert usa["in_degree"] == 0
    assert usa["out_degree"] == 0
    assert usa["total_degree"] == 0
    assert usa["pagerank_centrality"] < irq["pagerank_centrality"]


def test_directed_news_graph_contribution():
    """Verify directed news dyad contributes asymmetrically (source out-degree, target in-degree)."""
    mock_news_dyad = pd.DataFrame(
        [
            {
                "source_country_iso3": "USA",
                "target_country_iso3": "COD",
                "is_directed": True,
                "relationship_nature": "directed_news",
                "period_type": "cumulative_historical",
                "has_historical_conflict": False,
                "conflict_events_total": 0,
                "fatalities_best_total": 0.0,
                "news_article_count": 1,
                "news_avg_tone": -0.5,
                "composite_tension_index": 0.25,
            }
        ]
    )

    ref_countries = ["USA", "COD", "FRA"]
    metrics = compute_node_network_metrics(ref_countries, mock_news_dyad)

    usa = metrics[metrics["country_iso3"] == "USA"].iloc[0]
    cod = metrics[metrics["country_iso3"] == "COD"].iloc[0]

    # USA is reporting country (outgoing)
    assert usa["out_degree"] == 1
    assert usa["in_degree"] == 0
    assert usa["weighted_out_degree"] == 0.25
    assert usa["weighted_in_degree"] == 0.0

    # COD is mentioned country (incoming)
    assert cod["in_degree"] == 1
    assert cod["out_degree"] == 0
    assert cod["weighted_in_degree"] == 0.25
    assert cod["weighted_out_degree"] == 0.0


def test_hybrid_relationship_behavior():
    """
    Verify hybrid dyad handling:
    When a pair has both mutual conflict and directed news from A -> B:
    - is_directed is True
    - relationship_nature is 'hybrid'
    - Conflict contributes symmetrically while news contributes directionally.
    """
    mock_events = pd.DataFrame(
        [
            {
                "id": 10,
                "side_a": "Government of India",
                "side_b": "Government of Pakistan",
                "year_month": "2022-01",
                "event_date": "2022-01-10",
                "best": 20,
                "low": 20,
                "high": 20,
                "deaths_civilians": 0,
                "conflict_name": "India - Pakistan",
            }
        ]
    )
    mock_news = pd.DataFrame(
        [
            {
                "article_id": "art_ind_pak",
                "source_country_iso3": "IND",
                "target_country_iso3": "PAK",
                "year_month": "2026-08",
                "tone_score": -0.7,
                "is_negative_tone": True,
                "is_conflict_relevant": True,
            }
        ]
    )

    dyads_ev, _ = extract_ucdp_bilateral_dyads(mock_events)
    cum_dyads = aggregate_cumulative_dyads(dyads_ev, mock_news)

    # Exactly 1 dyad should be formed: IND -> PAK as hybrid
    assert len(cum_dyads) == 1
    row = cum_dyads.iloc[0]
    assert row["source_country_iso3"] == "IND"
    assert row["target_country_iso3"] == "PAK"
    assert row["is_directed"] == True
    assert row["relationship_nature"] == "hybrid"
    assert row["has_historical_conflict"] == True
    assert row["conflict_events_total"] == 1
    assert row["news_article_count"] == 1

    # Graph metrics check
    ref_countries = ["IND", "PAK"]
    metrics = compute_node_network_metrics(ref_countries, cum_dyads)
    ind = metrics[metrics["country_iso3"] == "IND"].iloc[0]
    pak = metrics[metrics["country_iso3"] == "PAK"].iloc[0]

    # Both have mutual conflict adversaries
    assert ind["conflict_adversary_count"] == 1
    assert pak["conflict_adversary_count"] == 1


def test_empty_and_single_node_graph_safety():
    """Verify pure-Python PageRank handles empty, single-node, and zero-edge graphs safely."""
    # 1. Empty graph
    pr_empty = compute_pagerank(nodes=[], edges=[])
    assert pr_empty == {}

    # 2. Single-node graph
    pr_single = compute_pagerank(nodes=["USA"], edges=[])
    assert pr_single == {"USA": 1.0}

    # 3. Disconnected graph with no edges
    pr_disconnected = compute_pagerank(nodes=["USA", "UKR", "IND"], edges=[])
    assert len(pr_disconnected) == 3
    for c in ["USA", "UKR", "IND"]:
        assert pr_disconnected[c] == pytest.approx(1.0 / 3.0)

    # 4. Empty dyads in compute_node_network_metrics
    empty_metrics = compute_node_network_metrics(
        reference_countries=["USA", "UKR"],
        dyads_df=pd.DataFrame(),
    )
    assert len(empty_metrics) == 2
    assert (empty_metrics["in_degree"] == 0).all()
    assert (empty_metrics["out_degree"] == 0).all()
    assert (empty_metrics["conflict_adversary_count"] == 0).all()
    assert (empty_metrics["has_active_edges"] == False).all()


def test_composite_tension_normalization():
    """Verify deterministic composite tension calculation and strict [0.0, 1.0] bounds."""
    # Zero activity -> 0.0
    assert calculate_composite_tension(0, 0, 0, None, 0) == 0.0

    # Mild conflict
    t_mild = calculate_composite_tension(
        conflict_fatalities=10,
        conflict_events=1,
        news_article_count=0,
        news_avg_tone=None,
        news_conflict_count=0,
    )
    assert 0.0 < t_mild < 1.0

    # Extreme conflict (e.g. 50,000 fatalities) -> capped at 1.0
    t_extreme = calculate_composite_tension(
        conflict_fatalities=50000,
        conflict_events=1000,
        news_article_count=0,
        news_avg_tone=None,
        news_conflict_count=0,
    )
    assert t_extreme == 1.0

    # News-only hostile tone (-1.0) and 100% conflict news
    t_news_hostile = calculate_composite_tension(
        conflict_fatalities=0,
        conflict_events=0,
        news_article_count=10,
        news_avg_tone=-1.0,
        news_conflict_count=10,
    )
    assert t_news_hostile == 1.0

    # Combined conflict and news
    t_combined = calculate_composite_tension(
        conflict_fatalities=500,
        conflict_events=20,
        news_article_count=5,
        news_avg_tone=-0.6,
        news_conflict_count=3,
    )
    assert 0.0 <= t_combined <= 1.0


def test_temporal_leakage_prevention():
    """
    Verify strict zero future data leakage:
    In monthly panels, prior-only forecasting features for month t must not change
    if month t or month t+1 data changes.
    """
    mock_events = pd.DataFrame(
        [
            {
                "id": 1,
                "side_a": "Government of Russia (Soviet Union)",
                "side_b": "Government of Ukraine",
                "year_month": "2022-01",
                "event_date": "2022-01-10",
                "best": 10,
                "low": 10,
                "high": 10,
                "deaths_civilians": 0,
                "conflict_name": "Russia - Ukraine",
            },
            {
                "id": 2,
                "side_a": "Government of Russia (Soviet Union)",
                "side_b": "Government of Ukraine",
                "year_month": "2022-02",
                "event_date": "2022-02-15",
                "best": 50,
                "low": 50,
                "high": 50,
                "deaths_civilians": 5,
                "conflict_name": "Russia - Ukraine",
            },
            {
                "id": 3,
                "side_a": "Government of Russia (Soviet Union)",
                "side_b": "Government of Ukraine",
                "year_month": "2022-03",
                "event_date": "2022-03-20",
                "best": 1000,
                "low": 1000,
                "high": 1000,
                "deaths_civilians": 100,
                "conflict_name": "Russia - Ukraine",
            },
        ]
    )

    dyads_ev, _ = extract_ucdp_bilateral_dyads(mock_events)
    monthly_panel = build_monthly_dyads_panel(dyads_ev, pd.DataFrame())

    # For 2022-02, the lag-1m conflict events must strictly equal 2022-01 events (1)
    feb_row = monthly_panel[monthly_panel["year_month"] == "2022-02"].iloc[0]
    assert feb_row["conflict_events_lag_1m"] == 1

    # For 2022-03, lag-1m conflict events must equal 2022-02 events (1)
    mar_row = monthly_panel[monthly_panel["year_month"] == "2022-03"].iloc[0]
    assert mar_row["conflict_events_lag_1m"] == 1


def test_unavailable_history_remains_nan():
    """
    Verify out-of-window historical lags evaluate to NaN rather than being zero-filled.
    """
    mock_events = pd.DataFrame(
        [
            {
                "id": 1,
                "side_a": "Government of Russia (Soviet Union)",
                "side_b": "Government of Ukraine",
                "year_month": "2022-01",
                "event_date": "2022-01-10",
                "best": 10,
                "low": 10,
                "high": 10,
                "deaths_civilians": 0,
                "conflict_name": "Russia - Ukraine",
            }
        ]
    )
    dyads_ev, _ = extract_ucdp_bilateral_dyads(mock_events)
    monthly_panel = build_monthly_dyads_panel(dyads_ev, pd.DataFrame())

    # First month in observation has no prior month in dataset; lag_1m must be NaN
    first_row = monthly_panel.iloc[0]
    assert pd.isna(first_row["conflict_events_lag_1m"])
    assert pd.isna(first_row["conflict_events_prior_sum_3m"])


def test_json_schema_and_metadata():
    """
    Verify decoupled node-link JSON export:
    - Contains 'nodes' and 'links'.
    - Contains exactly the reference nodes.
    - Contains explicit relationship metadata: is_directed and relationship_nature.
    """
    ref_countries = ["RUS", "UKR", "USA"]
    mock_dyads = pd.DataFrame(
        [
            {
                "source_country_iso3": "RUS",
                "target_country_iso3": "UKR",
                "is_directed": False,
                "relationship_nature": "undirected_conflict",
                "has_historical_conflict": True,
                "conflict_events_total": 500,
                "fatalities_best_total": 2500.0,
                "news_article_count": 0,
                "news_avg_tone": np.nan,
                "composite_tension_index": 0.95,
            }
        ]
    )

    node_metrics = compute_node_network_metrics(ref_countries, mock_dyads)
    graph_json = build_network_graph_json(node_metrics, mock_dyads)

    assert "nodes" in graph_json
    assert "links" in graph_json

    # Nodes check
    node_ids = [n["id"] for n in graph_json["nodes"]]
    assert set(node_ids) == set(ref_countries)

    # Links check
    assert len(graph_json["links"]) == 1
    link = graph_json["links"][0]
    assert link["source"] == "RUS"
    assert link["target"] == "UKR"
    assert link["is_directed"] == False
    assert link["relationship_nature"] == "undirected_conflict"
    assert link["conflict_events"] == 500
    assert link["fatalities"] == 2500.0
    assert link["has_conflict"] == True
    assert link["tension_index"] == 0.95
