"""
Unit tests for Member 3 Milestone 4: What-If Geopolitical Simulator.
Tests parameter validation, direct country/dyad shocks, relational ripple attenuation,
symmetric conflict vs directional news propagation, isolated node safety, PageRank conservation,
severance behavior, zero leakage, no fabricated edges, and deterministic reproducibility.
"""

from typing import Dict, List
import numpy as np
import pandas as pd
import pytest

from src.scenarios.config import (
    BASELINE_METRICS_PATH,
    BASELINE_DYADS_PATH,
    BASELINE_NEWS_PATH,
    BASELINE_SELECTION_RULE,
)
from src.scenarios.engine import ScenarioEngine
from src.scenarios.schema import ScenarioDefinition, SimulationResult


@pytest.fixture(scope="module")
def engine():
    """Shared ScenarioEngine instance loaded with real baseline data."""
    return ScenarioEngine()


def test_invalid_target_country_iso3(engine):
    """Verify validation raises ValueError on invalid or non-reference target country."""
    with pytest.raises(ValueError, match="Invalid target_country_iso3"):
        scen = ScenarioDefinition(
            scenario_id="test_invalid_country",
            name="Invalid Country Test",
            target_country_iso3="XYZ",  # Non-existent ISO3
        )
        engine.simulate(scen)

    with pytest.raises(ValueError, match="Invalid target_country_iso3"):
        scen_empty = ScenarioDefinition(
            scenario_id="test_empty",
            name="Empty Country Test",
            target_country_iso3="",
        )
        engine.simulate(scen_empty)


def test_invalid_target_dyad(engine):
    """Verify validation raises ValueError on malformed or invalid target dyads."""
    # Self-referential dyad
    with pytest.raises(ValueError, match="cannot be self-referential"):
        scen_self = ScenarioDefinition(
            scenario_id="test_self_dyad",
            name="Self Dyad Test",
            target_country_iso3="RUS",
            target_dyad=("RUS", "RUS"),
        )
        engine.simulate(scen_self)

    # Invalid country in dyad
    with pytest.raises(ValueError, match="must both be valid reference countries"):
        scen_invalid_c = ScenarioDefinition(
            scenario_id="test_invalid_dyad_c",
            name="Invalid Country Dyad Test",
            target_country_iso3="RUS",
            target_dyad=("RUS", "FAKE"),
        )
        engine.simulate(scen_invalid_c)


def test_tension_delta_requires_explicit_dyad(engine):
    """Verify tension_delta without target_dyad raises ValueError."""
    with pytest.raises(ValueError, match="tension_delta is only valid when target_dyad is explicitly provided"):
        scen = ScenarioDefinition(
            scenario_id="test_missing_dyad",
            name="Missing Dyad Test",
            target_country_iso3="IRN",
            tension_delta=0.3,
            target_dyad=None,  # Forbidden: cannot infer arbitrary dyad
        )
        engine.simulate(scen)


def test_multiplier_and_depth_validation(engine):
    """Verify negative multiplier, negative depth, and out-of-bounds decay factor raise ValueError."""
    # Negative multiplier
    with pytest.raises(ValueError, match="conflict_news_multiplier must be non-negative"):
        scen_neg_mult = ScenarioDefinition(
            scenario_id="test_neg_mult",
            name="Negative Multiplier Test",
            target_country_iso3="IRN",
            conflict_news_multiplier=-0.5,
        )
        engine.simulate(scen_neg_mult)

    # Negative depth
    with pytest.raises(ValueError, match="propagation_depth must be >= 0"):
        scen_neg_depth = ScenarioDefinition(
            scenario_id="test_neg_depth",
            name="Negative Depth Test",
            target_country_iso3="IRN",
            propagation_depth=-1,
        )
        engine.simulate(scen_neg_depth)

    # Decay factor out of bounds [0, 1]
    with pytest.raises(ValueError, match="decay_factor must be in"):
        scen_decay = ScenarioDefinition(
            scenario_id="test_decay",
            name="Decay Factor Test",
            target_country_iso3="IRN",
            decay_factor=1.5,
        )
        engine.simulate(scen_decay)


def test_severance_behavior(engine):
    """
    Verify severance:
    1. Requires explicit target_dyad.
    2. Cannot sever non-existent empirical dyad.
    3. Sets simulated dyadic tension to 0.0 and is_severed=True on valid dyad.
    """
    # Sever without dyad
    with pytest.raises(ValueError, match="sever_dyadic_tie requires an explicit target_dyad"):
        scen_no_dyad = ScenarioDefinition(
            scenario_id="test_sever_no_dyad",
            name="Sever No Dyad",
            target_country_iso3="IRN",
            sever_dyadic_tie=True,
            target_dyad=None,
        )
        engine.simulate(scen_no_dyad)

    # Sever non-existent empirical dyad
    with pytest.raises(ValueError, match="Cannot sever non-existent empirical dyad"):
        scen_non_existent = ScenarioDefinition(
            scenario_id="test_sever_non_existent",
            name="Sever Non-Existent Dyad",
            target_country_iso3="BRA",
            sever_dyadic_tie=True,
            target_dyad=("BRA", "IND"),  # BRA and IND are valid reference countries but no empirical dyad exists between them
        )
        engine.simulate(scen_non_existent)

    # Valid severance on active dyad (IRN, ISR)
    scen_valid = ScenarioDefinition(
        scenario_id="test_valid_sever",
        name="Valid Severance",
        target_country_iso3="IRN",
        sever_dyadic_tie=True,
        target_dyad=("IRN", "ISR"),
        propagation_depth=0,
    )
    res = engine.simulate(scen_valid)
    severed_dyads = [d for d in res.dyad_impacts if d["is_severed"]]
    assert len(severed_dyads) >= 1
    for d in severed_dyads:
        assert d["counterfactual_tension_index"] == 0.0


def test_tone_and_tension_bounds_clipping(engine):
    """Verify massive shocks are clipped strictly to [-1.0, 1.0] for tone and [0.0, 1.0] for tension."""
    # Massive negative tone shock
    scen_extreme_neg = ScenarioDefinition(
        scenario_id="test_extreme_neg",
        name="Extreme Neg Tone",
        target_country_iso3="RUS",
        tone_delta=-10.0,
        propagation_depth=0,
    )
    res_neg = engine.simulate(scen_extreme_neg)
    tgt_neg = next(c for c in res_neg.country_impacts if c["country_iso3"] == "RUS")
    assert tgt_neg["counterfactual_tone"] == -1.0

    # Massive positive tone shock
    scen_extreme_pos = ScenarioDefinition(
        scenario_id="test_extreme_pos",
        name="Extreme Pos Tone",
        target_country_iso3="RUS",
        tone_delta=10.0,
        propagation_depth=0,
    )
    res_pos = engine.simulate(scen_extreme_pos)
    tgt_pos = next(c for c in res_pos.country_impacts if c["country_iso3"] == "RUS")
    assert tgt_pos["counterfactual_tone"] == 1.0

    # Tension delta bounds on dyad
    scen_tens_up = ScenarioDefinition(
        scenario_id="test_tens_up",
        name="Tension Up",
        target_country_iso3="IRN",
        target_dyad=("IRN", "ISR"),
        tension_delta=5.0,
        propagation_depth=0,
    )
    res_tens = engine.simulate(scen_tens_up)
    dyad_tens = next(d for d in res_tens.dyad_impacts if (d["source_country_iso3"], d["target_country_iso3"]) == ("IRN", "ISR") or (d["source_country_iso3"], d["target_country_iso3"]) == ("ISR", "IRN"))
    assert dyad_tens["counterfactual_tension_index"] <= 1.0


def test_direct_shock_calculation(engine):
    """Verify direct country-level shock modifies target country and records delta accurately."""
    scen = ScenarioDefinition(
        scenario_id="test_direct_shock",
        name="Direct Shock Test",
        target_country_iso3="IND",
        tone_delta=-0.3,
        conflict_news_multiplier=2.0,
        propagation_depth=0,
    )
    res = engine.simulate(scen)
    tgt = next(c for c in res.country_impacts if c["country_iso3"] == "IND")

    assert tgt["is_direct_target"] is True
    assert tgt["ripple_hop"] == 0
    assert tgt["delta_tone"] == -0.3
    assert tgt["counterfactual_conflict_news_count"] == tgt["baseline_conflict_news_count"] * 2


def test_zero_depth_propagation(engine):
    """Verify propagation_depth=0 confines shock strictly to target country (zero ripple)."""
    scen = ScenarioDefinition(
        scenario_id="test_zero_depth",
        name="Zero Depth Test",
        target_country_iso3="RUS",
        tone_delta=-0.5,
        propagation_depth=0,
    )
    res = engine.simulate(scen)

    for c in res.country_impacts:
        if c["country_iso3"] == "RUS":
            assert c["is_direct_target"] is True
            assert c["delta_tone"] == -0.5
        else:
            assert c["is_direct_target"] is False
            assert c["ripple_hop"] == -1
            assert c["delta_tone"] == 0.0


def test_first_hop_and_second_hop_decay(engine):
    """Verify network ripple decays with hop distance: hop 1 delta > hop 2 delta."""
    scen = ScenarioDefinition(
        scenario_id="test_ripple_decay",
        name="Ripple Decay Test",
        target_country_iso3="IRQ",  # Connected to KWT, USA, GBR, AUS
        tone_delta=-0.6,
        conflict_news_multiplier=2.0,
        propagation_depth=2,
        decay_factor=0.5,
    )
    res = engine.simulate(scen)

    hop1_countries = [c for c in res.country_impacts if c["ripple_hop"] == 1]
    hop2_countries = [c for c in res.country_impacts if c["ripple_hop"] == 2]

    assert len(hop1_countries) >= 1
    # Check that 1st-hop countries experienced ripple impact
    for c in hop1_countries:
        assert c["delta_tone"] != 0.0 or c["delta_pagerank"] != 0.0

    # If 2nd-hop countries exist, their delta must be attenuated compared to 1st-hop
    if hop2_countries:
        max_hop1_delta = max(abs(c["delta_tone"]) for c in hop1_countries)
        max_hop2_delta = max(abs(c["delta_tone"]) for c in hop2_countries)
        assert max_hop1_delta >= max_hop2_delta


def test_disconnected_node_receives_zero_ripple(engine):
    """Verify disconnected/isolated nodes with no path to target country receive zero ripple."""
    scen = ScenarioDefinition(
        scenario_id="test_isolated_node",
        name="Isolated Node Test",
        target_country_iso3="ECU",  # Only connected to PER
        tone_delta=-0.5,
        propagation_depth=2,
        decay_factor=0.5,
    )
    res = engine.simulate(scen)

    # An isolated African or Asian country not connected to ECU (e.g., AGO, ARG, BDI)
    ago = next(c for c in res.country_impacts if c["country_iso3"] == "AGO")
    assert ago["ripple_hop"] == -1
    assert ago["delta_tone"] == 0.0
    assert ago["delta_pagerank"] == 0.0


def test_symmetric_conflict_propagation(engine):
    """Verify mutual conflict relationship propagates symmetrically between both belligerents."""
    # Target KWT in conflict with IRQ
    scen_kwt = ScenarioDefinition(
        scenario_id="test_sym_kwt",
        name="Symmetric KWT Shock",
        target_country_iso3="KWT",
        tone_delta=-0.4,
        propagation_depth=1,
        decay_factor=0.5,
    )
    res = engine.simulate(scen_kwt)
    irq = next(c for c in res.country_impacts if c["country_iso3"] == "IRQ")
    # IRQ is direct conflict partner of KWT and must be reached at hop 1
    assert irq["ripple_hop"] == 1
    assert irq["delta_tone"] != 0.0


def test_directional_news_propagation(engine):
    """Verify directed news dyad propagates along edge direction (source -> target)."""
    # IND reports on UKR (IND -> UKR). Shocking IND should propagate to UKR.
    scen_ind = ScenarioDefinition(
        scenario_id="test_dir_ind",
        name="Directional IND Shock",
        target_country_iso3="IND",
        tone_delta=-0.5,
        propagation_depth=1,
        decay_factor=0.5,
    )
    res = engine.simulate(scen_ind)
    ukr = next(c for c in res.country_impacts if c["country_iso3"] == "UKR")
    # UKR receives incoming news from IND -> must be reached at hop 1
    assert ukr["ripple_hop"] == 1


def test_pagerank_sum_conservation(engine):
    """Verify counterfactual PageRank sum over all 125 countries equals 1.0 within numerical tolerance."""
    scen = ScenarioDefinition(
        scenario_id="test_pr_sum",
        name="PageRank Sum Test",
        target_country_iso3="IRN",
        tone_delta=-0.5,
        conflict_news_multiplier=1.5,
        propagation_depth=2,
    )
    res = engine.simulate(scen)
    pr_sum = sum(c["counterfactual_pagerank"] for c in res.country_impacts)
    assert pr_sum == pytest.approx(1.0, abs=1e-4)


def test_baseline_metadata_and_no_future_leakage(engine):
    """Verify simulation metadata records baseline period, selection rule, and source datasets."""
    scen = ScenarioDefinition(
        scenario_id="test_metadata",
        name="Metadata Test",
        target_country_iso3="USA",
    )
    res = engine.simulate(scen)
    meta = res.baseline_metadata

    assert "baseline_period" in meta
    assert meta["baseline_period"] == "2026-09"
    assert "baseline_selection_rule" in meta
    assert len(meta["source_datasets_used"]) == 3
    assert "forecasting_safety_disclaimer" in res.summary


def test_no_fabricated_or_new_edges(engine):
    """Verify simulation does not fabricate any new edges; links count matches baseline dyads count."""
    scen = ScenarioDefinition(
        scenario_id="test_no_new_edges",
        name="No New Edges Test",
        target_country_iso3="RUS",
        tone_delta=-0.4,
        propagation_depth=2,
    )
    res = engine.simulate(scen)
    assert len(res.graph_json["links"]) == len(engine.df_dyads)
    assert len(res.dyad_impacts) == len(engine.df_dyads)


def test_deterministic_reproducibility(engine):
    """Verify running simulation twice with identical parameters produces bit-for-bit identical outputs."""
    scen = ScenarioDefinition(
        scenario_id="test_reproducibility",
        name="Reproducibility Test",
        target_country_iso3="IRN",
        tone_delta=-0.3,
        conflict_news_multiplier=1.4,
        propagation_depth=2,
        decay_factor=0.5,
    )
    res1 = engine.simulate(scen)
    res2 = engine.simulate(scen)

    for c1, c2 in zip(res1.country_impacts, res2.country_impacts):
        assert c1["counterfactual_pagerank"] == c2["counterfactual_pagerank"]
        assert c1["counterfactual_tone"] == c2["counterfactual_tone"]
        assert c1["delta_tone"] == c2["delta_tone"]
        assert c1["ripple_hop"] == c2["ripple_hop"]
