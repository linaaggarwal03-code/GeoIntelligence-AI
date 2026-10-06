"""
What-If Geopolitical Simulator Core Engine (Member 3 Milestone 4).
Performs transparent, deterministic counterfactual scenario propagation using empirical baseline signals.
Simulates direct country/dyad shocks, relational network ripple effects, and recomputes graph metrics.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from src.relationships.config import ISO3_TO_COUNTRY_NAME, PAGERANK_ALPHA, PAGERANK_MAX_ITER, PAGERANK_TOL
from src.relationships.graph_builder import compute_pagerank
from src.scenarios.config import (
    BASELINE_METRICS_PATH,
    BASELINE_DYADS_PATH,
    BASELINE_NEWS_PATH,
    BASELINE_UCDP_PATH,
    BASELINE_NEWS_MONTH,
    BASELINE_UCDP_MONTH,
    BASELINE_SELECTION_RULE,
)
from src.scenarios.schema import ScenarioDefinition, SimulationResult

logger = logging.getLogger(__name__)


class ScenarioEngine:
    """
    Deterministic Counterfactual Scenario Engine.

    Disclaimer:
    This engine performs deterministic scenario shock propagation based on empirical baseline observations.
    It is NOT an empirical machine learning forecasting model and NOT an exact future-event predictor.
    """

    def __init__(
        self,
        metrics_path: Optional[Path] = None,
        dyads_path: Optional[Path] = None,
        news_path: Optional[Path] = None,
        ucdp_path: Optional[Path] = None,
    ):
        self.metrics_path = metrics_path or BASELINE_METRICS_PATH
        self.dyads_path = dyads_path or BASELINE_DYADS_PATH
        self.news_path = news_path or BASELINE_NEWS_PATH
        self.ucdp_path = ucdp_path or BASELINE_UCDP_PATH

        self._load_baseline_data()

    def _load_baseline_data(self) -> None:
        """
        Load validated empirical baseline datasets.
        """
        logger.info("Loading baseline datasets for scenario engine...")

        if not self.metrics_path.exists():
            raise FileNotFoundError(f"Baseline network metrics file not found: {self.metrics_path}")
        if not self.dyads_path.exists():
            raise FileNotFoundError(f"Baseline dyads file not found: {self.dyads_path}")
        if not self.news_path.exists():
            raise FileNotFoundError(f"Baseline news panel file not found: {self.news_path}")

        self.df_metrics = pd.read_parquet(self.metrics_path)
        self.df_dyads = pd.read_parquet(self.dyads_path)
        df_news = pd.read_parquet(self.news_path)

        # Baseline news state: latest complete calendar month (2026-09)
        self.df_news_baseline = df_news[df_news["year_month"] == BASELINE_NEWS_MONTH].copy()
        if self.df_news_baseline.empty:
            # Fallback to latest available month if 2026-09 not present
            latest_month = sorted(df_news["year_month"].unique())[-1]
            self.df_news_baseline = df_news[df_news["year_month"] == latest_month].copy()
            self.baseline_news_month = latest_month
        else:
            self.baseline_news_month = BASELINE_NEWS_MONTH

        # 125 Reference countries
        self.reference_countries = sorted(self.df_metrics["country_iso3"].unique().tolist())
        self.valid_dyad_pairs = list(
            zip(self.df_dyads["source_country_iso3"], self.df_dyads["target_country_iso3"])
        )

        logger.info(
            "Scenario engine initialized with %d reference countries and %d empirical dyads. Baseline news month: %s.",
            len(self.reference_countries),
            len(self.valid_dyad_pairs),
            self.baseline_news_month,
        )

    def simulate(self, scenario: ScenarioDefinition) -> SimulationResult:
        """
        Execute deterministic counterfactual scenario simulation.

        Steps:
        1. Validate scenario parameters against domain rules and reference data.
        2. Establish baseline country and dyad states.
        3. Apply direct country or dyad shocks (tone delta, news multiplier, tension delta, severance).
        4. Propagate relational ripple effects up to propagation_depth hops.
        5. Recalculate counterfactual graph topology and PageRank across all 125 countries.
        6. Compute exact baseline vs. counterfactual deltas and assemble SimulationResult.
        """
        # 1. Validation
        scenario.validate(self.reference_countries, self.valid_dyad_pairs)
        logger.info("Executing simulation for scenario: '%s' on target '%s'...", scenario.scenario_id, scenario.target_country_iso3)

        target_iso = scenario.target_country_iso3

        # 2. Build working copy of baseline country state
        news_map = {
            row["country_iso3"]: {
                "news_count": int(row.get("news_count_total", 0)),
                "avg_tone": float(row.get("avg_tone", 0.0) or 0.0),
                "conflict_news_count": int(row.get("conflict_news_count", 0)),
                "escalation_signal": float(row.get("escalation_signal", 0.0) or 0.0),
            }
            for _, row in self.df_news_baseline.iterrows()
        }

        # Node containers: iso3 -> dict
        country_state: Dict[str, Dict[str, Any]] = {}
        for _, row in self.df_metrics.iterrows():
            iso = row["country_iso3"]
            n_data = news_map.get(iso, {"news_count": 0, "avg_tone": 0.0, "conflict_news_count": 0, "escalation_signal": 0.0})

            country_state[iso] = {
                "country_iso3": iso,
                "country_name": row["country_name"],
                "is_direct_target": (iso == target_iso),
                "ripple_hop": 0 if iso == target_iso else -1,
                # Baseline metrics
                "baseline_tone": n_data["avg_tone"],
                "baseline_conflict_news_count": n_data["conflict_news_count"],
                "baseline_escalation_signal": n_data["escalation_signal"],
                "baseline_pagerank": float(row["pagerank_centrality"]),
                "baseline_in_degree": int(row["in_degree"]),
                "baseline_out_degree": int(row["out_degree"]),
                "baseline_total_degree": int(row["total_degree"]),
                "baseline_weighted_in": float(row["weighted_in_degree"]),
                "baseline_weighted_out": float(row["weighted_out_degree"]),
                # Counterfactual state (initialized to baseline)
                "counterfactual_tone": n_data["avg_tone"],
                "counterfactual_conflict_news_count": n_data["conflict_news_count"],
                "counterfactual_escalation_signal": n_data["escalation_signal"],
                "counterfactual_pagerank": float(row["pagerank_centrality"]),
                "counterfactual_in_degree": int(row["in_degree"]),
                "counterfactual_out_degree": int(row["out_degree"]),
                "counterfactual_total_degree": int(row["total_degree"]),
                "counterfactual_weighted_in": float(row["weighted_in_degree"]),
                "counterfactual_weighted_out": float(row["weighted_out_degree"]),
            }

        # 3. Build working copy of baseline dyads
        dyad_state: List[Dict[str, Any]] = []
        for _, row in self.df_dyads.iterrows():
            src = row["source_country_iso3"]
            dst = row["target_country_iso3"]
            tens = float(row["composite_tension_index"])
            is_dir = bool(row["is_directed"])
            rel_nat = str(row["relationship_nature"])

            dyad_state.append(
                {
                    "source_country_iso3": src,
                    "target_country_iso3": dst,
                    "is_directed": is_dir,
                    "relationship_nature": rel_nat,
                    "baseline_tension_index": tens,
                    "counterfactual_tension_index": tens,
                    "is_severed": False,
                    "is_directly_shocked": False,
                    "is_ripple_affected": False,
                    "has_historical_conflict": bool(row.get("has_historical_conflict", False)),
                    "fatalities_best_total": float(row.get("fatalities_best_total", 0.0)),
                    "news_avg_tone": row.get("news_avg_tone"),
                }
            )

        # 4. Apply Direct Shocks
        # 4A. Target country direct shock
        tgt_state = country_state[target_iso]
        # Tone shock clipped to [-1.0, 1.0]
        tgt_state["counterfactual_tone"] = float(np.clip(tgt_state["baseline_tone"] + scenario.tone_delta, -1.0, 1.0))
        # Conflict news shock
        tgt_state["counterfactual_conflict_news_count"] = max(
            0, int(round(tgt_state["baseline_conflict_news_count"] * scenario.conflict_news_multiplier))
        )
        # Shift escalation signal if tone or news worsened
        news_ratio_shift = (scenario.conflict_news_multiplier - 1.0) * 0.2
        tone_neg_shift = max(0.0, -scenario.tone_delta) * 0.3
        tgt_state["counterfactual_escalation_signal"] = float(
            np.clip(tgt_state["baseline_escalation_signal"] + news_ratio_shift + tone_neg_shift, 0.0, 1.0)
        )

        # Determine direct tension shift magnitude
        if scenario.tension_delta is not None:
            direct_tension_delta = scenario.tension_delta
        else:
            # Country-level shock converts to direct tension impact on incident ties
            tone_impact = -scenario.tone_delta * 0.5  # Negative tone increases tension
            news_impact = (scenario.conflict_news_multiplier - 1.0) * 0.2
            direct_tension_delta = float(tone_impact + news_impact)

        # 4B. Dyad direct shock (if explicit target_dyad provided)
        if scenario.target_dyad is not None:
            c_a, c_b = scenario.target_dyad[0], scenario.target_dyad[1]
            for d in dyad_state:
                # Matches either directed or canonical undirected
                match_dir = (d["source_country_iso3"] == c_a and d["target_country_iso3"] == c_b)
                match_undir = (
                    not d["is_directed"]
                    and (
                        (d["source_country_iso3"] == c_a and d["target_country_iso3"] == c_b)
                        or (d["source_country_iso3"] == c_b and d["target_country_iso3"] == c_a)
                    )
                )

                if match_dir or match_undir:
                    d["is_directly_shocked"] = True
                    if scenario.sever_dyadic_tie:
                        d["is_severed"] = True
                        d["counterfactual_tension_index"] = 0.0
                    elif scenario.tension_delta is not None:
                        d["counterfactual_tension_index"] = float(
                            np.clip(d["baseline_tension_index"] + scenario.tension_delta, 0.0, 1.0)
                        )

        # 5. Relational Ripple Propagation
        # Formula: delta_neighbor = direct_delta * decay_factor * normalized_edge_weight
        if scenario.propagation_depth > 0 and abs(direct_tension_delta) > 1e-4:
            self._propagate_network_ripple(
                target_iso=target_iso,
                direct_tension_delta=direct_tension_delta,
                propagation_depth=scenario.propagation_depth,
                decay_factor=scenario.decay_factor,
                country_state=country_state,
                dyad_state=dyad_state,
            )

        # 6. Topological Recalculation (PageRank, degrees)
        self._recalculate_network_metrics(country_state, dyad_state)

        # 7. Compute Final Deltas & Assemble Result
        country_impacts_list = []
        for iso in self.reference_countries:
            c = country_state[iso]
            c["delta_tone"] = round(c["counterfactual_tone"] - c["baseline_tone"], 4)
            c["delta_conflict_news_count"] = c["counterfactual_conflict_news_count"] - c["baseline_conflict_news_count"]
            c["delta_escalation_signal"] = round(c["counterfactual_escalation_signal"] - c["baseline_escalation_signal"], 4)
            c["delta_pagerank"] = round(c["counterfactual_pagerank"] - c["baseline_pagerank"], 6)
            c["delta_in_degree"] = c["counterfactual_in_degree"] - c["baseline_in_degree"]
            c["delta_out_degree"] = c["counterfactual_out_degree"] - c["baseline_out_degree"]
            c["delta_total_degree"] = c["counterfactual_total_degree"] - c["baseline_total_degree"]
            c["delta_weighted_in"] = round(c["counterfactual_weighted_in"] - c["baseline_weighted_in"], 4)
            c["delta_weighted_out"] = round(c["counterfactual_weighted_out"] - c["baseline_weighted_out"], 4)
            country_impacts_list.append(c)

        for d in dyad_state:
            d["delta_tension_index"] = round(d["counterfactual_tension_index"] - d["baseline_tension_index"], 4)

        # Build scenario graph JSON
        graph_json = self._serialize_scenario_graph(country_impacts_list, dyad_state)

        # Build simulation summary
        baseline_meta = {
            "baseline_period": self.baseline_news_month,
            "baseline_selection_rule": BASELINE_SELECTION_RULE,
            "source_datasets_used": [
                str(self.metrics_path.name),
                str(self.dyads_path.name),
                str(self.news_path.name),
            ],
            "source_coverage": {
                "news_panel": "2026-07 to 2026-10 (baseline selected: 2026-09)",
                "ucdp_panel": "1989-01 to 2025-12 (baseline selected: 2025-12)",
                "relationship_network": "Cumulative empirical cross-sectional graph",
            },
        }

        # Calculate statistics
        affected_countries = [c for c in country_impacts_list if c["is_direct_target"] or c["ripple_hop"] > 0]
        max_pr_up = max(country_impacts_list, key=lambda x: x["delta_pagerank"])
        max_pr_down = min(country_impacts_list, key=lambda x: x["delta_pagerank"])

        summary = {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.name,
            "description": scenario.description,
            "target_country_iso3": scenario.target_country_iso3,
            "target_dyad": scenario.target_dyad,
            "archetype": scenario.archetype,
            "baseline_metadata": baseline_meta,
            "parameters": {
                "tone_delta": scenario.tone_delta,
                "conflict_news_multiplier": scenario.conflict_news_multiplier,
                "tension_delta": scenario.tension_delta,
                "sever_dyadic_tie": scenario.sever_dyadic_tie,
                "propagation_depth": scenario.propagation_depth,
                "decay_factor": scenario.decay_factor,
            },
            "simulation_statistics": {
                "total_reference_countries": len(self.reference_countries),
                "directly_shocked_countries": 1,
                "ripple_affected_countries_count": len(affected_countries) - 1,
                "total_affected_countries_count": len(affected_countries),
                "unaffected_countries_count": len(self.reference_countries) - len(affected_countries),
                "total_dyads_simulated": len(dyad_state),
                "severed_dyads_count": sum(1 for d in dyad_state if d["is_severed"]),
                "max_pagerank_increase": {
                    "country_iso3": max_pr_up["country_iso3"],
                    "delta_pagerank": max_pr_up["delta_pagerank"],
                },
                "max_pagerank_decrease": {
                    "country_iso3": max_pr_down["country_iso3"],
                    "delta_pagerank": max_pr_down["delta_pagerank"],
                },
            },
            "forecasting_safety_disclaimer": (
                "This simulation is a deterministic counterfactual scenario analysis based on observed historical and recent baseline signals. "
                "It is not an empirical machine learning prediction, not a forecast of future news volume, and not an exact future-event predictor."
            ),
            "simulated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        return SimulationResult(
            scenario=scenario,
            baseline_metadata=baseline_meta,
            country_impacts=country_impacts_list,
            dyad_impacts=dyad_state,
            graph_json=graph_json,
            summary=summary,
        )

    def _propagate_network_ripple(
        self,
        target_iso: str,
        direct_tension_delta: float,
        propagation_depth: int,
        decay_factor: float,
        country_state: Dict[str, Dict[str, Any]],
        dyad_state: List[Dict[str, Any]],
    ) -> None:
        """
        Propagate deterministic counterfactual tension ripple across empirical graph edges.

        Rules:
        - Mutual conflict edges propagate symmetrically (A <-> B).
        - Directed news edges propagate along the edge direction (source -> target).
        - Disconnected/isolated nodes receive zero ripple.
        - Attenuation formula: delta_neighbor = direct_delta * decay_factor * (W_uv / sum_W_uk).
        """
        # Build adjacency mapping: node -> list of (neighbor_iso, dyad_dict, direction_weight)
        adjacency: Dict[str, List[Tuple[str, Dict[str, Any], float]]] = {
            c: [] for c in self.reference_countries
        }

        for d in dyad_state:
            if d["is_severed"]:
                continue
            src, dst = d["source_country_iso3"], d["target_country_iso3"]
            tens = d["baseline_tension_index"]

            if src not in adjacency or dst not in adjacency:
                continue

            if not d["is_directed"] or d["relationship_nature"] == "undirected_conflict":
                # Mutual conflict: symmetric propagation both ways
                adjacency[src].append((dst, d, tens))
                adjacency[dst].append((src, d, tens))
            elif d["relationship_nature"] == "hybrid":
                # Hybrid: propagates both ways (conflict symmetric + news directed)
                adjacency[src].append((dst, d, tens))
                adjacency[dst].append((src, d, tens * 0.5))
            else:
                # Directed news: propagates source -> target
                adjacency[src].append((dst, d, tens))

        # BFS Queue: (current_node, delta_at_node, current_hop)
        visited: Dict[str, int] = {target_iso: 0}
        queue: List[Tuple[str, float, int]] = [(target_iso, direct_tension_delta, 0)]

        while queue:
            curr_node, curr_delta, curr_hop = queue.pop(0)

            if curr_hop >= propagation_depth:
                continue

            neighbors = adjacency.get(curr_node, [])
            if not neighbors:
                continue

            total_weight = sum(w for _, _, w in neighbors)
            if total_weight <= 0:
                total_weight = float(len(neighbors))

            for nbr_iso, dyad_ref, w in neighbors:
                if nbr_iso in visited and visited[nbr_iso] <= curr_hop:
                    continue

                norm_w = (w / total_weight) if total_weight > 0 else (1.0 / len(neighbors))
                delta_nbr = curr_delta * decay_factor * norm_w

                next_hop = curr_hop + 1
                visited[nbr_iso] = next_hop

                # Update neighbor country state
                nbr_state = country_state[nbr_iso]
                if nbr_state["ripple_hop"] == -1 or nbr_state["ripple_hop"] > next_hop:
                    nbr_state["ripple_hop"] = next_hop

                # Shift neighbor's counterfactual tone proportionally (inverse to tension shock)
                tone_shift = -np.sign(delta_nbr) * min(0.4, abs(delta_nbr))
                nbr_state["counterfactual_tone"] = float(
                    np.clip(nbr_state["counterfactual_tone"] + tone_shift, -1.0, 1.0)
                )

                # Update dyad tension
                if not dyad_ref["is_directly_shocked"] and not dyad_ref["is_severed"]:
                    dyad_ref["is_ripple_affected"] = True
                    dyad_ref["counterfactual_tension_index"] = float(
                        np.clip(dyad_ref["counterfactual_tension_index"] + delta_nbr, 0.0, 1.0)
                    )

                # Continue propagation to next hop
                queue.append((nbr_iso, delta_nbr, next_hop))

    def _recalculate_network_metrics(
        self,
        country_state: Dict[str, Dict[str, Any]],
        dyad_state: List[Dict[str, Any]],
    ) -> None:
        """
        Recalculate counterfactual graph topology (degrees, weighted strengths, PageRank)
        over the complete 125-country reference universe.
        """
        n_total = len(self.reference_countries)

        in_deg = {c: 0 for c in self.reference_countries}
        out_deg = {c: 0 for c in self.reference_countries}
        weighted_in = {c: 0.0 for c in self.reference_countries}
        weighted_out = {c: 0.0 for c in self.reference_countries}
        adj_partners: Dict[str, Set[str]] = {c: set() for c in self.reference_countries}

        edges_for_pr: List[Tuple[str, str, float]] = []

        for d in dyad_state:
            if d["is_severed"]:
                continue

            src = d["source_country_iso3"]
            dst = d["target_country_iso3"]
            if src not in adj_partners or dst not in adj_partners:
                continue

            weight = float(d["counterfactual_tension_index"])
            if weight <= 0.0:
                continue

            is_dir = d["is_directed"]
            rel_nat = d["relationship_nature"]

            if not is_dir or rel_nat == "undirected_conflict":
                # Symmetric mutual conflict
                adj_partners[src].add(dst)
                adj_partners[dst].add(src)

                in_deg[src] += 1
                out_deg[src] += 1
                in_deg[dst] += 1
                out_deg[dst] += 1

                weighted_in[src] += weight
                weighted_out[src] += weight
                weighted_in[dst] += weight
                weighted_out[dst] += weight

                edges_for_pr.append((src, dst, weight))
                edges_for_pr.append((dst, src, weight))

            elif rel_nat == "hybrid":
                # Hybrid: src -> dst full; dst -> src conflict portion
                adj_partners[src].add(dst)
                adj_partners[dst].add(src)

                out_deg[src] += 1
                in_deg[src] += 1
                in_deg[dst] += 1
                out_deg[dst] += 1

                c_weight = weight * 0.7  # conflict weight portion
                weighted_out[src] += weight
                weighted_in[dst] += weight
                weighted_out[dst] += c_weight
                weighted_in[src] += c_weight

                edges_for_pr.append((src, dst, weight))
                edges_for_pr.append((dst, src, c_weight))

            else:
                # Directed news: src -> dst
                adj_partners[src].add(dst)
                adj_partners[dst].add(src)

                out_deg[src] += 1
                in_deg[dst] += 1

                weighted_out[src] += weight
                weighted_in[dst] += weight

                edges_for_pr.append((src, dst, weight))

        # PageRank power iteration
        pr_scores = compute_pagerank(
            nodes=self.reference_countries,
            edges=edges_for_pr,
            alpha=PAGERANK_ALPHA,
            max_iter=PAGERANK_MAX_ITER,
            tol=PAGERANK_TOL,
        )

        for c in self.reference_countries:
            st = country_state[c]
            st["counterfactual_in_degree"] = in_deg[c]
            st["counterfactual_out_degree"] = out_deg[c]
            st["counterfactual_total_degree"] = len(adj_partners[c])
            st["counterfactual_weighted_in"] = round(weighted_in[c], 4)
            st["counterfactual_weighted_out"] = round(weighted_out[c], 4)
            st["counterfactual_pagerank"] = round(pr_scores.get(c, 1.0 / n_total), 6)

    def _serialize_scenario_graph(
        self,
        country_impacts: List[Dict[str, Any]],
        dyad_impacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Serialize counterfactual graph to decoupled node-link JSON showing baseline vs counterfactual metrics.
        """
        nodes = [
            {
                "id": c["country_iso3"],
                "label": c["country_name"],
                "is_direct_target": c["is_direct_target"],
                "ripple_hop": c["ripple_hop"],
                "baseline_pagerank": c["baseline_pagerank"],
                "counterfactual_pagerank": c["counterfactual_pagerank"],
                "delta_pagerank": c["delta_pagerank"],
                "baseline_tone": c["baseline_tone"],
                "counterfactual_tone": c["counterfactual_tone"],
                "delta_tone": c["delta_tone"],
                "total_degree": c["counterfactual_total_degree"],
            }
            for c in country_impacts
        ]

        links = [
            {
                "source": d["source_country_iso3"],
                "target": d["target_country_iso3"],
                "is_directed": d["is_directed"],
                "relationship_nature": d["relationship_nature"],
                "baseline_tension": d["baseline_tension_index"],
                "counterfactual_tension": d["counterfactual_tension_index"],
                "delta_tension": d["delta_tension_index"],
                "is_severed": d["is_severed"],
                "is_directly_shocked": d["is_directly_shocked"],
                "is_ripple_affected": d["is_ripple_affected"],
            }
            for d in dyad_impacts
        ]

        return {"nodes": nodes, "links": links}
