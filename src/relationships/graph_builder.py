"""
Graph construction and network topological metrics module for GeoIntelligence AI.
Computes in/out degree, weighted degree strength, PageRank centrality,
and serializes decoupled node-link JSON graphs without external heavy graph dependencies.

Symmetric & Directed Semantics:
- Bilateral armed conflict is mutual/undirected: contributes symmetrically to both belligerents
  in degree, weighted degree, and reciprocal PageRank transitions.
- GDELT news attention is directed: source_country_iso3 (publisher) emits outgoing degree/tone,
  and target_country_iso3 receives incoming degree/tone.
- Hybrid dyads contribute symmetrically for conflict and directionally for news.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd

from src.relationships.config import (
    ISO3_TO_COUNTRY_NAME,
    PAGERANK_ALPHA,
    PAGERANK_MAX_ITER,
    PAGERANK_TOL,
)

logger = logging.getLogger(__name__)


def compute_pagerank(
    nodes: Sequence[str],
    edges: Sequence[Tuple[str, str, float]],
    alpha: float = PAGERANK_ALPHA,
    max_iter: int = PAGERANK_MAX_ITER,
    tol: float = PAGERANK_TOL,
) -> Dict[str, float]:
    """
    Compute PageRank centrality for a directed, weighted graph using standard power iteration.
    Zero external graph dependencies (pure NumPy implementation).

    Edge case handling:
    - Empty graph: returns empty dict.
    - Single-node graph: returns {node: 1.0}.
    - Disconnected components / isolated nodes: receives uniform teleportation probability (1/N).
    - Dangling nodes (out-degree = 0): distributed uniformly across all nodes.
    """
    node_list = list(dict.fromkeys(nodes))
    n = len(node_list)

    if n == 0:
        return {}
    if n == 1:
        return {node_list[0]: 1.0}

    node_to_idx = {node: i for i, node in enumerate(node_list)}
    idx_to_node = {i: node for i, node in enumerate(node_list)}

    # Construct weighted transition matrix
    # W[i, j] = weight of edge from i to j
    W = np.zeros((n, n), dtype=np.float64)
    for src, dst, weight in edges:
        if src in node_to_idx and dst in node_to_idx and weight > 0:
            i, j = node_to_idx[src], node_to_idx[dst]
            W[i, j] += weight

    # Compute row sums (out-degree strength)
    row_sums = W.sum(axis=1)

    # Transition probability matrix M
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        if row_sums[i] > 0:
            M[i, :] = W[i, :] / row_sums[i]
        else:
            # Dangling node: teleports uniformly
            M[i, :] = 1.0 / n

    # Power iteration
    # p is row vector: p_{k+1} = alpha * p_k * M + (1 - alpha) / n
    p = np.full(n, 1.0 / n, dtype=np.float64)
    uniform_teleport = (1.0 - alpha) / n

    for iteration in range(max_iter):
        p_next = alpha * np.dot(p, M) + uniform_teleport
        diff = np.sum(np.abs(p_next - p))
        p = p_next
        if diff < tol:
            break

    # Normalize to ensure sum is exactly 1.0
    total_p = np.sum(p)
    if total_p > 0:
        p = p / total_p

    return {idx_to_node[i]: float(p[i]) for i in range(n)}


def compute_node_network_metrics(
    reference_countries: List[str],
    dyads_df: pd.DataFrame,
    weight_col: str = "composite_tension_index",
) -> pd.DataFrame:
    """
    Compute country-level topological and relational network metrics.

    Correctness & Directionality:
    - Bilateral armed conflict (is_directed=False):
      Contributes symmetrically to both countries (mutual conflict).
      Both participants receive in-degree, out-degree, and reciprocal PageRank transitions.
      No arbitrary aggressor direction is invented.
    - Directed news coverage (is_directed=True, relationship_nature='directed_news'):
      Reporting country emits out-degree and outgoing tone.
      Mentioned country receives in-degree and incoming tone.
    - Hybrid relationships:
      Conflict component contributes symmetrically, news component contributes directionally.
    - conflict_adversary_count: Count of sovereign state adversaries with bilateral armed conflict.
    - total_degree: Count of unique distinct adjacent partner countries.
    - Isolated nodes: Handled safely with degree 0, weighted degree 0.0, adversary count 0,
      uniform PageRank (1/N), and NaN for tone.
    """
    n_total = len(reference_countries)
    logger.info("Computing network metrics across %d reference countries...", n_total)

    in_degree: Dict[str, int] = {c: 0 for c in reference_countries}
    out_degree: Dict[str, int] = {c: 0 for c in reference_countries}
    weighted_in: Dict[str, float] = {c: 0.0 for c in reference_countries}
    weighted_out: Dict[str, float] = {c: 0.0 for c in reference_countries}
    adjacent_partners: Dict[str, Set[str]] = {c: set() for c in reference_countries}
    conflict_adversaries: Dict[str, Set[str]] = {c: set() for c in reference_countries}
    incoming_tones: Dict[str, List[float]] = {c: [] for c in reference_countries}
    outgoing_tones: Dict[str, List[float]] = {c: [] for c in reference_countries}
    incident_tensions: Dict[str, List[float]] = {c: [] for c in reference_countries}

    edges_for_pagerank: List[Tuple[str, str, float]] = []

    if not dyads_df.empty:
        for _, row in dyads_df.iterrows():
            src = str(row.get("source_country_iso3", ""))
            dst = str(row.get("target_country_iso3", ""))
            weight = float(row.get(weight_col, 0.0) or 0.0)

            is_directed = bool(row.get("is_directed", True))
            rel_nature = str(row.get("relationship_nature", "directed_news"))
            has_conflict = bool(row.get("has_historical_conflict", False))
            tone = row.get("news_avg_tone")
            tone_val = float(tone) if pd.notna(tone) else None

            # 1. Conflict Adversary Tracking (always symmetric between the two states)
            if has_conflict:
                if src in conflict_adversaries:
                    conflict_adversaries[src].add(dst)
                if dst in conflict_adversaries:
                    conflict_adversaries[dst].add(src)

            # 2. Graph Topology & Degree Contribution
            if not is_directed or rel_nature == "undirected_conflict":
                # UNDIRECTED CONFLICT: Mutual relationship between src and dst
                # Contributes symmetrically to both belligerents
                if src in in_degree and dst in in_degree:
                    # Incident partners
                    adjacent_partners[src].add(dst)
                    adjacent_partners[dst].add(src)

                    # Symmetric degrees
                    in_degree[src] += 1
                    out_degree[src] += 1
                    in_degree[dst] += 1
                    out_degree[dst] += 1

                    # Symmetric weighted degrees
                    weighted_in[src] += weight
                    weighted_out[src] += weight
                    weighted_in[dst] += weight
                    weighted_out[dst] += weight

                    incident_tensions[src].append(weight)
                    incident_tensions[dst].append(weight)

                    # Symmetric reciprocal edges for PageRank power iteration
                    if weight > 0:
                        edges_for_pagerank.append((src, dst, weight))
                        edges_for_pagerank.append((dst, src, weight))

            elif rel_nature == "hybrid":
                # HYBRID: Directed news from src -> dst combined with mutual conflict
                if src in in_degree and dst in in_degree:
                    adjacent_partners[src].add(dst)
                    adjacent_partners[dst].add(src)

                    # Degrees: src has out (news+conflict) and in (mutual conflict)
                    out_degree[src] += 1
                    in_degree[src] += 1
                    in_degree[dst] += 1
                    out_degree[dst] += 1

                    weighted_out[src] += weight
                    weighted_in[dst] += weight
                    # Mutual conflict portion from dst to src
                    conflict_portion = float(row.get("fatalities_best_total", 0.0))
                    c_weight = weight if conflict_portion > 0 else 0.5 * weight
                    weighted_out[dst] += c_weight
                    weighted_in[src] += c_weight

                    incident_tensions[src].append(weight)
                    incident_tensions[dst].append(weight)

                    if tone_val is not None:
                        outgoing_tones[src].append(tone_val)
                        incoming_tones[dst].append(tone_val)

                    if weight > 0:
                        edges_for_pagerank.append((src, dst, weight))
                        edges_for_pagerank.append((dst, src, c_weight))

            else:
                # DIRECTED NEWS: Reporting country src -> Target country dst
                if src in out_degree and dst in in_degree:
                    adjacent_partners[src].add(dst)
                    adjacent_partners[dst].add(src)

                    out_degree[src] += 1
                    in_degree[dst] += 1

                    weighted_out[src] += weight
                    weighted_in[dst] += weight

                    incident_tensions[src].append(weight)
                    incident_tensions[dst].append(weight)

                    if tone_val is not None:
                        outgoing_tones[src].append(tone_val)
                        incoming_tones[dst].append(tone_val)

                    if weight > 0:
                        edges_for_pagerank.append((src, dst, weight))

    # Compute PageRank on directed graph
    pagerank_scores = compute_pagerank(
        nodes=reference_countries,
        edges=edges_for_pagerank,
        alpha=PAGERANK_ALPHA,
        max_iter=PAGERANK_MAX_ITER,
        tol=PAGERANK_TOL,
    )

    # Assemble records
    records = []
    for c in reference_countries:
        in_deg = in_degree[c]
        out_deg = out_degree[c]
        tot_deg = len(adjacent_partners[c])

        inc_tones = incoming_tones[c]
        out_tones = outgoing_tones[c]
        inc_tensions = incident_tensions[c]

        mean_inc_tone = float(np.mean(inc_tones)) if inc_tones else np.nan
        mean_out_tone = float(np.mean(out_tones)) if out_tones else np.nan
        mean_tens = float(np.mean(inc_tensions)) if inc_tensions else 0.0

        records.append(
            {
                "country_iso3": c,
                "country_name": ISO3_TO_COUNTRY_NAME.get(c, c),
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": tot_deg,
                "weighted_in_degree": round(weighted_in[c], 4),
                "weighted_out_degree": round(weighted_out[c], 4),
                "conflict_adversary_count": len(conflict_adversaries[c]),
                "pagerank_centrality": round(pagerank_scores.get(c, 1.0 / n_total), 6),
                "mean_incoming_tone": round(mean_inc_tone, 4) if pd.notna(mean_inc_tone) else np.nan,
                "mean_outgoing_tone": round(mean_out_tone, 4) if pd.notna(mean_out_tone) else np.nan,
                "mean_dyadic_tension": round(mean_tens, 4),
                "has_active_edges": tot_deg > 0,
            }
        )

    metrics_df = pd.DataFrame(records).sort_values(
        ["pagerank_centrality", "total_degree"], ascending=[False, False]
    ).reset_index(drop=True)

    return metrics_df


def build_network_graph_json(
    nodes_df: pd.DataFrame,
    dyads_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Serialize empirical relationship network into standard decoupled node-link JSON.

    Format includes explicit relationship metadata:
    - is_directed (bool): True for directed news/hybrid, False for mutual conflict
    - relationship_nature (str): 'undirected_conflict' | 'directed_news' | 'hybrid'
    """
    nodes_list: List[Dict[str, Any]] = []
    for _, row in nodes_df.iterrows():
        nodes_list.append(
            {
                "id": str(row["country_iso3"]),
                "label": str(row["country_name"]),
                "in_degree": int(row["in_degree"]),
                "out_degree": int(row["out_degree"]),
                "total_degree": int(row["total_degree"]),
                "conflict_adversaries": int(row["conflict_adversary_count"]),
                "pagerank": float(row["pagerank_centrality"]),
                "mean_dyadic_tension": float(row["mean_dyadic_tension"]),
                "has_active_edges": bool(row["has_active_edges"]),
            }
        )

    links_list: List[Dict[str, Any]] = []
    if not dyads_df.empty:
        for _, row in dyads_df.iterrows():
            tone_val = row.get("news_avg_tone")
            avg_tone = float(tone_val) if pd.notna(tone_val) else None

            links_list.append(
                {
                    "source": str(row["source_country_iso3"]),
                    "target": str(row["target_country_iso3"]),
                    "is_directed": bool(row.get("is_directed", False)),
                    "relationship_nature": str(row.get("relationship_nature", "undirected_conflict")),
                    "conflict_events": int(row.get("conflict_events_total", 0)),
                    "fatalities": float(row.get("fatalities_best_total", 0.0)),
                    "news_articles": int(row.get("news_article_count", 0)),
                    "avg_tone": avg_tone,
                    "tension_index": float(round(row.get("composite_tension_index", 0.0), 4)),
                    "has_conflict": bool(row.get("has_historical_conflict", False)),
                }
            )

    return {
        "nodes": nodes_list,
        "links": links_list,
    }
