"""
Dyad extraction and empirical relationship feature module for GeoIntelligence AI.
Extracts bilateral state dyads from UCDP conflict events and directed news dyads from GDELT DOC 2.0.
Computes deterministic, transparent relationship features and temporal lag/rolling features.

Semantic Corrections:
- UCDP bilateral armed conflict is treated as mutual/undirected between sovereign state pairs.
  Raw UCDP side_a / side_b does not denote an aggressor or one-way directionality.
- Canonical alphabetical ordering min(A, B) and max(A, B) is used for undirected conflict dyads.
- GDELT news dyads are strictly directed: source_country_iso3 (reporting publisher) -> target_country_iso3 (entity).
- Relationship metadata:
  - is_directed (bool)
  - relationship_nature ("undirected_conflict", "directed_news", "hybrid")
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from src.relationships.config import (
    UCDP_GOV_NAME_TO_ISO3,
    TENSION_WEIGHT_CONFLICT,
    TENSION_WEIGHT_NEWS,
    FATALITIES_LOG_SCALE,
    LAG_MONTHS,
    ROLLING_WINDOWS,
)

logger = logging.getLogger(__name__)


def parse_government_entities(text: Optional[str]) -> List[str]:
    """
    Extract recognized sovereign state ISO 3166-1 alpha-3 codes from UCDP participant strings.
    Matches standard UCDP format: 'Government of <Entity>'.
    Handles multilateral coalitions by parsing all occurrences.
    Returns a deduplicated list of resolved ISO-3 country codes.
    If no recognized state government is found, returns an empty list.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    # Match all instances of "Government of <Entity>" (up to comma, semicolon, or end of string)
    matches = re.findall(r"Government of ([^,;\n]+)", text)
    iso3_codes: List[str] = []

    for entity in matches:
        clean_name = entity.strip()
        iso = UCDP_GOV_NAME_TO_ISO3.get(clean_name)
        if iso and iso not in iso3_codes:
            iso3_codes.append(iso)

    return iso3_codes


def extract_ucdp_bilateral_dyads(
    events_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Extract only reliably identifiable bilateral state dyads from UCDP GED events.

    Correctness Requirements:
    - Only construct a bilateral state dyad when the event record provides sufficient
      evidence that both participants can be reliably mapped to distinct country ISO-3 codes.
    - If a record cannot be reliably mapped, exclude it from bilateral dyad extraction
      and record the exclusion count in metadata.
    - Non-state rebel/insurgent groups (e.g., FARC, Syrian insurgents) are excluded
      from bilateral state dyad extraction as they are intrastate non-state actors.
    - Bilateral state conflict is semantically mutual/undirected: endpoints are canonicalized
      alphabetically (min(A, B), max(A, B)) so no artificial initiator/aggressor direction is invented.
    - Handles multilateral state coalitions on either side by generating all pairwise
      combinations (A_i, B_j) where A_i != B_j.

    Returns:
        (dyad_events_df, exclusion_stats)
    """
    total_events = len(events_df)
    logger.info("Extracting bilateral state dyads from %d UCDP event records...", total_events)

    if events_df.empty:
        empty_df = pd.DataFrame(
            columns=[
                "event_id",
                "country_a_iso3",
                "country_b_iso3",
                "source_country_iso3",
                "target_country_iso3",
                "is_directed",
                "relationship_nature",
                "year_month",
                "event_date",
                "fatalities_best",
                "fatalities_low",
                "fatalities_high",
                "deaths_civilians",
                "conflict_name",
            ]
        )
        return empty_df, {
            "total_events_processed": 0,
            "bilateral_events_retained": 0,
            "intrastate_civil_events_excluded": 0,
            "unmapped_events_excluded": 0,
        }

    # Optimization: Filter events where side_b contains "Government of"
    gov_b_mask = events_df["side_b"].str.contains("Government of", na=False)
    candidate_df = events_df[gov_b_mask].copy()

    intrastate_excluded = total_events - len(candidate_df)
    unmapped_excluded = 0
    bilateral_records: List[Dict[str, Any]] = []

    for _, row in candidate_df.iterrows():
        side_a_text = row.get("side_a")
        side_b_text = row.get("side_b")

        side_a_isos = parse_government_entities(side_a_text)
        side_b_isos = parse_government_entities(side_b_text)

        if not side_a_isos or not side_b_isos:
            unmapped_excluded += 1
            continue

        event_id = row.get("id")
        year_month = str(row.get("year_month", ""))
        event_date = row.get("event_date")
        best = float(row.get("best", 0.0) or 0.0)
        low = float(row.get("low", 0.0) or 0.0)
        high = float(row.get("high", 0.0) or 0.0)
        civilians = float(row.get("deaths_civilians", 0.0) or 0.0)
        conflict_name = str(row.get("conflict_name", ""))

        # Form dyadic pairs with canonical alphabetical ordering for undirected conflict
        valid_pair_found = False
        for a_iso in side_a_isos:
            for b_iso in side_b_isos:
                if a_iso != b_iso:
                    valid_pair_found = True
                    c_a, c_b = (a_iso, b_iso) if a_iso < b_iso else (b_iso, a_iso)
                    bilateral_records.append(
                        {
                            "event_id": event_id,
                            "country_a_iso3": c_a,
                            "country_b_iso3": c_b,
                            "source_country_iso3": c_a,
                            "target_country_iso3": c_b,
                            "is_directed": False,
                            "relationship_nature": "undirected_conflict",
                            "year_month": year_month,
                            "event_date": event_date,
                            "fatalities_best": best,
                            "fatalities_low": low,
                            "fatalities_high": high,
                            "deaths_civilians": civilians,
                            "conflict_name": conflict_name,
                        }
                    )

        if not valid_pair_found:
            unmapped_excluded += 1

    dyad_events_df = pd.DataFrame(bilateral_records)
    retained_events_count = len(candidate_df) - unmapped_excluded

    exclusion_stats = {
        "total_events_processed": int(total_events),
        "bilateral_candidate_events": int(len(candidate_df)),
        "bilateral_events_retained": int(retained_events_count),
        "bilateral_dyad_observations_extracted": int(len(dyad_events_df)),
        "intrastate_civil_events_excluded": int(intrastate_excluded),
        "unmapped_events_excluded": int(unmapped_excluded),
        "total_excluded_records": int(intrastate_excluded + unmapped_excluded),
    }

    logger.info(
        "Bilateral extraction complete: %d dyad observations extracted from %d retained events (%d excluded).",
        len(dyad_events_df),
        retained_events_count,
        exclusion_stats["total_excluded_records"],
    )

    return dyad_events_df, exclusion_stats


def extract_news_dyads(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract directed empirical news dyads from cleaned GDELT DOC 2.0 articles.

    Correctness Requirement:
    - Use source_country_iso3 strictly as the reporting/source country (publisher origin).
    - Use target_country_iso3 strictly as the target/entity country (mentioned conflict zone).
    - Never reverse or merge these meanings.
    - Discard unassigned/low-confidence target entities (None) and intra-country articles (source == target).
    - Sets is_directed=True and relationship_nature='directed_news'.
    """
    if news_df.empty:
        return pd.DataFrame(
            columns=[
                "source_country_iso3",
                "target_country_iso3",
                "is_directed",
                "relationship_nature",
                "year_month",
                "news_article_count",
                "news_avg_tone",
                "news_negative_tone_count",
                "news_negative_tone_share",
                "news_conflict_article_count",
                "news_conflict_ratio",
            ]
        )

    # Filter for valid directed dyads
    valid_mask = (
        news_df["source_country_iso3"].notna()
        & news_df["target_country_iso3"].notna()
        & (news_df["source_country_iso3"] != news_df["target_country_iso3"])
    )
    df_valid = news_df[valid_mask].copy()

    if df_valid.empty:
        return pd.DataFrame(
            columns=[
                "source_country_iso3",
                "target_country_iso3",
                "is_directed",
                "relationship_nature",
                "year_month",
                "news_article_count",
                "news_avg_tone",
                "news_negative_tone_count",
                "news_negative_tone_share",
                "news_conflict_article_count",
                "news_conflict_ratio",
            ]
        )

    # Group by directed dyad and month
    grouped = df_valid.groupby(
        ["source_country_iso3", "target_country_iso3", "year_month"], as_index=False
    ).agg(
        news_article_count=("article_id", "count"),
        news_avg_tone=("tone_score", "mean"),
        news_negative_tone_count=("is_negative_tone", "sum"),
        news_conflict_article_count=("is_conflict_relevant", "sum"),
    )

    # Metadata
    grouped["is_directed"] = True
    grouped["relationship_nature"] = "directed_news"

    # Safe ratio derivations
    grouped["news_negative_tone_share"] = np.where(
        grouped["news_article_count"] > 0,
        grouped["news_negative_tone_count"] / grouped["news_article_count"],
        0.0,
    )
    grouped["news_conflict_ratio"] = np.where(
        grouped["news_article_count"] > 0,
        grouped["news_conflict_article_count"] / grouped["news_article_count"],
        0.0,
    )

    return grouped


def calculate_composite_tension(
    conflict_fatalities: float,
    conflict_events: int,
    news_article_count: int,
    news_avg_tone: Optional[float],
    news_conflict_count: int,
) -> float:
    """
    Calculate empirical Composite Tension Index in range [0.0, 1.0].

    Transparent, deterministic formula:
    1. Conflict Intensity Component (S_conflict):
       - Logarithmic scaling of fatalities normalized against 1000 fatalities threshold:
         S_conflict = min(1.0, ln(1 + fatalities) / ln(1 + 1000))
       - If zero fatalities but conflict events > 0, base level of 0.25 is assigned.
    2. News Hostility Component (S_news):
       - Negative tone intensity: max(0.0, -avg_tone) since tone in [-1.0, 1.0].
       - Conflict article share: conflict_count / article_count.
       - S_news = 0.5 * negative_tone_intensity + 0.5 * conflict_share.
    3. Composite Index:
       - If both conflict and news are present: 0.6 * S_conflict + 0.4 * S_news.
       - If only conflict is present: S_conflict.
       - If only news is present: S_news.
       - If neither: 0.0.

    Note: This is an analytical project-derived metric, not an official UCDP/GDELT definition.
    """
    has_conflict = conflict_events > 0 or conflict_fatalities > 0
    has_news = news_article_count > 0

    if not has_conflict and not has_news:
        return 0.0

    # 1. Conflict score
    s_conflict = 0.0
    if has_conflict:
        if conflict_fatalities > 0:
            s_conflict = float(
                min(
                    1.0,
                    np.log1p(conflict_fatalities) / np.log1p(FATALITIES_LOG_SCALE),
                )
            )
        else:
            s_conflict = 0.25

    # 2. News score
    s_news = 0.0
    if has_news:
        tone_val = float(news_avg_tone) if news_avg_tone is not None and not np.isnan(news_avg_tone) else 0.0
        neg_tone_intensity = max(0.0, -tone_val)
        conflict_share = news_conflict_count / max(1, news_article_count)
        s_news = float(np.clip(0.5 * neg_tone_intensity + 0.5 * conflict_share, 0.0, 1.0))

    # 3. Combine
    if has_conflict and has_news:
        tension = (TENSION_WEIGHT_CONFLICT * s_conflict) + (TENSION_WEIGHT_NEWS * s_news)
    elif has_conflict:
        tension = s_conflict
    else:
        tension = s_news

    return float(np.clip(tension, 0.0, 1.0))


def aggregate_cumulative_dyads(
    ucdp_events_df: pd.DataFrame,
    news_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate all historical UCDP bilateral conflict events and GDELT news dyads
    into a comprehensive cumulative dyadic relationship table.

    Semantic Requirements:
    - UCDP bilateral armed conflict: is_directed=False, relationship_nature='undirected_conflict'
      Stored with canonical alphabetical endpoints min(A, B) and max(A, B).
    - GDELT news dyads: is_directed=True, relationship_nature='directed_news'
      Stored with source_country_iso3 (reporting country) and target_country_iso3 (entity).
    - If a pair has both empirical conflict and directed news:
      Represented with relationship_nature='hybrid', is_directed=True (directed news component
      from source to target combined with mutual conflict history).
    """
    # 1. Aggregate UCDP events by canonical unordered pair
    conflict_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    if not ucdp_events_df.empty:
        # Canonicalize endpoints
        events_copy = ucdp_events_df.copy()
        if "country_a_iso3" not in events_copy.columns:
            events_copy["c_a"] = events_copy.apply(
                lambda r: min(r["source_country_iso3"], r["target_country_iso3"]), axis=1
            )
            events_copy["c_b"] = events_copy.apply(
                lambda r: max(r["source_country_iso3"], r["target_country_iso3"]), axis=1
            )
        else:
            events_copy["c_a"] = events_copy["country_a_iso3"]
            events_copy["c_b"] = events_copy["country_b_iso3"]

        ucdp_grouped = events_copy.groupby(["c_a", "c_b"], as_index=False).agg(
            conflict_events=("event_id", "count"),
            fatalities_best=("fatalities_best", "sum"),
            fatalities_low=("fatalities_low", "sum"),
            fatalities_high=("fatalities_high", "sum"),
            deaths_civilians=("deaths_civilians", "sum"),
        )

        for _, row in ucdp_grouped.iterrows():
            pair_key = (row["c_a"], row["c_b"])
            conflict_map[pair_key] = {
                "source_country_iso3": pair_key[0],
                "target_country_iso3": pair_key[1],
                "is_directed": False,
                "relationship_nature": "undirected_conflict",
                "period_type": "cumulative_historical",
                "has_historical_conflict": True,
                "conflict_events_total": int(row["conflict_events"]),
                "fatalities_best_total": float(row["fatalities_best"]),
                "fatalities_low_total": float(row["fatalities_low"]),
                "fatalities_high_total": float(row["fatalities_high"]),
                "deaths_civilians_total": float(row["deaths_civilians"]),
                "news_article_count": 0,
                "news_avg_tone": np.nan,
                "news_negative_tone_count": 0,
                "news_negative_tone_share": 0.0,
                "news_conflict_article_count": 0,
                "news_conflict_ratio": 0.0,
            }

    # 2. Aggregate GDELT news dyads (strictly directed)
    news_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    news_dyads = extract_news_dyads(news_df)

    if not news_dyads.empty:
        news_cum = news_dyads.groupby(
            ["source_country_iso3", "target_country_iso3"], as_index=False
        ).agg(
            news_article_count=("news_article_count", "sum"),
            news_avg_tone=("news_avg_tone", "mean"),
            news_negative_tone_count=("news_negative_tone_count", "sum"),
            news_conflict_article_count=("news_conflict_article_count", "sum"),
        )

        for _, row in news_cum.iterrows():
            dir_key = (row["source_country_iso3"], row["target_country_iso3"])
            art_count = int(row["news_article_count"])
            neg_count = int(row["news_negative_tone_count"])
            conf_count = int(row["news_conflict_article_count"])
            tone = float(row["news_avg_tone"]) if pd.notna(row["news_avg_tone"]) else np.nan

            news_map[dir_key] = {
                "news_article_count": art_count,
                "news_avg_tone": tone,
                "news_negative_tone_count": neg_count,
                "news_negative_tone_share": neg_count / max(1, art_count),
                "news_conflict_article_count": conf_count,
                "news_conflict_ratio": conf_count / max(1, art_count),
            }

    # 3. Combine into final records handling undirected conflict, directed news, and hybrid
    final_records: List[Dict[str, Any]] = []
    consumed_conflict_pairs: Set[Tuple[str, str]] = set()

    # Process all directed news dyads
    for (src, dst), n_data in news_map.items():
        canonical_conflict_key = (min(src, dst), max(src, dst))

        if canonical_conflict_key in conflict_map:
            # HYBRID relationship: Pair has mutual conflict AND directed news from src -> dst
            consumed_conflict_pairs.add(canonical_conflict_key)
            c_data = conflict_map[canonical_conflict_key]

            rec = {
                "source_country_iso3": src,
                "target_country_iso3": dst,
                "is_directed": True,
                "relationship_nature": "hybrid",
                "period_type": "cumulative_historical",
                "has_historical_conflict": True,
                "conflict_events_total": c_data["conflict_events_total"],
                "fatalities_best_total": c_data["fatalities_best_total"],
                "fatalities_low_total": c_data["fatalities_low_total"],
                "fatalities_high_total": c_data["fatalities_high_total"],
                "deaths_civilians_total": c_data["deaths_civilians_total"],
                "news_article_count": n_data["news_article_count"],
                "news_avg_tone": n_data["news_avg_tone"],
                "news_negative_tone_count": n_data["news_negative_tone_count"],
                "news_negative_tone_share": n_data["news_negative_tone_share"],
                "news_conflict_article_count": n_data["news_conflict_article_count"],
                "news_conflict_ratio": n_data["news_conflict_ratio"],
            }
        else:
            # DIRECTED NEWS relationship
            rec = {
                "source_country_iso3": src,
                "target_country_iso3": dst,
                "is_directed": True,
                "relationship_nature": "directed_news",
                "period_type": "cumulative_historical",
                "has_historical_conflict": False,
                "conflict_events_total": 0,
                "fatalities_best_total": 0.0,
                "fatalities_low_total": 0.0,
                "fatalities_high_total": 0.0,
                "deaths_civilians_total": 0.0,
                "news_article_count": n_data["news_article_count"],
                "news_avg_tone": n_data["news_avg_tone"],
                "news_negative_tone_count": n_data["news_negative_tone_count"],
                "news_negative_tone_share": n_data["news_negative_tone_share"],
                "news_conflict_article_count": n_data["news_conflict_article_count"],
                "news_conflict_ratio": n_data["news_conflict_ratio"],
            }
        final_records.append(rec)

    # Process all pure UNDIRECTED CONFLICT dyads that had no overlapping news coverage
    for pair_key, c_data in conflict_map.items():
        if pair_key not in consumed_conflict_pairs:
            final_records.append(c_data)

    # 4. Compute composite tension for all active dyads
    for rec in final_records:
        rec["composite_tension_index"] = calculate_composite_tension(
            conflict_fatalities=rec["fatalities_best_total"],
            conflict_events=rec["conflict_events_total"],
            news_article_count=rec["news_article_count"],
            news_avg_tone=rec["news_avg_tone"],
            news_conflict_count=rec["news_conflict_article_count"],
        )

    if not final_records:
        return pd.DataFrame(
            columns=[
                "source_country_iso3",
                "target_country_iso3",
                "is_directed",
                "relationship_nature",
                "period_type",
                "has_historical_conflict",
                "conflict_events_total",
                "fatalities_best_total",
                "fatalities_low_total",
                "fatalities_high_total",
                "deaths_civilians_total",
                "news_article_count",
                "news_avg_tone",
                "news_negative_tone_count",
                "news_negative_tone_share",
                "news_conflict_article_count",
                "news_conflict_ratio",
                "composite_tension_index",
            ]
        )

    df_result = pd.DataFrame(final_records).sort_values(
        ["composite_tension_index", "source_country_iso3"], ascending=[False, True]
    ).reset_index(drop=True)

    return df_result


def build_monthly_dyads_panel(
    ucdp_events_df: pd.DataFrame,
    news_df: pd.DataFrame,
    observed_news_months: Optional[Set[str]] = None,
) -> pd.DataFrame:
    """
    Build monthly dyadic observations with strict separation of current-month descriptive
    signals and prior-only forecasting features.

    Temporal Safety Requirements:
    - Current month t metrics describe month t.
    - Prior forecasting features for month t strictly use information from t-1, t-2, t-3.
    - Preserves NaN for unavailable historical periods outside the observed coverage.
    - Genuine zeros within the observed coverage remain 0.0.
    """
    # 1. Aggregate UCDP by canonical dyad and month
    ucdp_monthly = pd.DataFrame()
    if not ucdp_events_df.empty:
        events_copy = ucdp_events_df.copy()
        if "country_a_iso3" not in events_copy.columns:
            events_copy["c_a"] = events_copy.apply(
                lambda r: min(r["source_country_iso3"], r["target_country_iso3"]), axis=1
            )
            events_copy["c_b"] = events_copy.apply(
                lambda r: max(r["source_country_iso3"], r["target_country_iso3"]), axis=1
            )
        else:
            events_copy["c_a"] = events_copy["country_a_iso3"]
            events_copy["c_b"] = events_copy["country_b_iso3"]

        ucdp_monthly = events_copy.groupby(
            ["c_a", "c_b", "year_month"], as_index=False
        ).agg(
            conflict_events_monthly=("event_id", "count"),
            fatalities_best_monthly=("fatalities_best", "sum"),
        ).rename(columns={"c_a": "source_country_iso3", "c_b": "target_country_iso3"})
        ucdp_monthly["is_directed"] = False
        ucdp_monthly["relationship_nature"] = "undirected_conflict"

    # 2. Extract news monthly dyads (strictly directed)
    news_monthly = extract_news_dyads(news_df)

    # 3. Combine active dyads across months
    merged = pd.merge(
        ucdp_monthly,
        news_monthly,
        on=["source_country_iso3", "target_country_iso3", "year_month"],
        how="outer",
    )

    if merged.empty:
        return pd.DataFrame(
            columns=[
                "source_country_iso3",
                "target_country_iso3",
                "is_directed",
                "relationship_nature",
                "year_month",
                "conflict_events_monthly",
                "fatalities_best_monthly",
                "news_article_count_monthly",
                "news_avg_tone_monthly",
                "news_conflict_count_monthly",
                "monthly_tension_index",
            ]
        )

    # Resolve is_directed and relationship_nature
    has_conf = merged["conflict_events_monthly"].notna() & (merged["conflict_events_monthly"] > 0)
    has_news = (
        merged["news_article_count"].notna() & (merged["news_article_count"] > 0)
        if "news_article_count" in merged.columns
        else pd.Series(False, index=merged.index)
    )

    nature_series = []
    directed_series = []
    for c, n in zip(has_conf, has_news):
        if c and n:
            nature_series.append("hybrid")
            directed_series.append(True)
        elif n:
            nature_series.append("directed_news")
            directed_series.append(True)
        else:
            nature_series.append("undirected_conflict")
            directed_series.append(False)

    merged["is_directed"] = directed_series
    merged["relationship_nature"] = nature_series

    merged["conflict_events_monthly"] = merged["conflict_events_monthly"].fillna(0).astype(int)
    merged["fatalities_best_monthly"] = merged["fatalities_best_monthly"].fillna(0.0)
    merged["news_article_count_monthly"] = (
        merged["news_article_count"].fillna(0).astype(int)
        if "news_article_count" in merged.columns
        else 0
    )
    merged["news_avg_tone_monthly"] = (
        merged["news_avg_tone"] if "news_avg_tone" in merged.columns else np.nan
    )
    merged["news_conflict_count_monthly"] = (
        merged["news_conflict_article_count"].fillna(0).astype(int)
        if "news_conflict_article_count" in merged.columns
        else 0
    )

    # Compute monthly tension index
    tension_series = []
    for _, row in merged.iterrows():
        t = calculate_composite_tension(
            conflict_fatalities=row["fatalities_best_monthly"],
            conflict_events=row["conflict_events_monthly"],
            news_article_count=row["news_article_count_monthly"],
            news_avg_tone=row["news_avg_tone_monthly"],
            news_conflict_count=row["news_conflict_count_monthly"],
        )
        tension_series.append(t)
    merged["monthly_tension_index"] = tension_series

    # Clean unneeded intermediate columns
    drop_cols = [
        c
        for c in [
            "news_article_count",
            "news_avg_tone",
            "news_negative_tone_count",
            "news_negative_tone_share",
            "news_conflict_article_count",
            "news_conflict_ratio",
            "is_directed_x",
            "is_directed_y",
            "relationship_nature_x",
            "relationship_nature_y",
        ]
        if c in merged.columns
    ]
    if drop_cols:
        merged = merged.drop(columns=drop_cols)

    # 4. Compute temporal lag/rolling features per dyad
    # Sort chronologically
    merged = merged.sort_values(
        ["source_country_iso3", "target_country_iso3", "year_month"]
    ).reset_index(drop=True)

    # Prior-only lags (shift by 1)
    grouped_dyad = merged.groupby(["source_country_iso3", "target_country_iso3"])

    # Lag 1 month (strictly prior information)
    merged["monthly_tension_lag_1m"] = grouped_dyad["monthly_tension_index"].shift(1)
    merged["conflict_events_lag_1m"] = grouped_dyad["conflict_events_monthly"].shift(1)
    merged["news_count_lag_1m"] = grouped_dyad["news_article_count_monthly"].shift(1)

    # Prior 3-month rolling sum (requires full support: min_periods=3)
    merged["conflict_events_prior_sum_3m"] = (
        grouped_dyad["conflict_events_monthly"]
        .shift(1)
        .rolling(window=3, min_periods=3)
        .sum()
    )

    return merged
