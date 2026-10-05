"""
Unit and integration tests for Member 3 Milestone 2: News Intelligence & NLP Pipeline.
Tests timestamp normalization, article deduplication, source vs. target country decoupling,
conflict taxonomy classification, lexical tone scoring, zero-division safety,
and temporal leakage prevention.
"""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest

from src.news.config import CONFLICT_TAXONOMY
from src.news.normalize import (
    generate_article_id,
    parse_gdelt_timestamp,
    resolve_source_country,
    resolve_target_country,
    normalize_articles,
)
from src.news.conflict_classifier import classify_conflict_relevance
from src.news.nlp_signals import compute_lexical_tone
from src.news.country_month_agg import (
    safe_relative_growth,
    aggregate_country_month_news,
    compute_time_aware_news_features,
)


def test_gdelt_timestamp_parsing():
    """Verify UTC normalization of GDELT's 'YYYYMMDDTHHMMSSZ' format."""
    dt, ym = parse_gdelt_timestamp("20260813T024500Z")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 8
    assert dt.day == 13
    assert dt.hour == 2
    assert dt.minute == 45
    assert dt.tzinfo == timezone.utc
    assert ym == "2026-08"

    # Edge cases
    assert parse_gdelt_timestamp("")[0] is None
    assert parse_gdelt_timestamp("invalid_date")[0] is None


def test_article_deduplication():
    """Verify duplicate removal based on hash and same-day identical headlines."""
    raw_articles = [
        {
            "url": "https://reuters.com/world/article-1",
            "title": "Sudan peace talks resume in Jeddah",
            "seendate": "20260715T100000Z",
            "domain": "reuters.com",
            "language": "English",
            "sourcecountry": "United States",
        },
        # Exact duplicate
        {
            "url": "https://reuters.com/world/article-1",
            "title": "Sudan peace talks resume in Jeddah",
            "seendate": "20260715T100000Z",
            "domain": "reuters.com",
            "language": "English",
            "sourcecountry": "United States",
        },
        # Same headline on same day from syndicated mirror
        {
            "url": "https://yahoo.com/news/article-1-mirror",
            "title": "Sudan peace talks resume in Jeddah",
            "seendate": "20260715T123000Z",
            "domain": "yahoo.com",
            "language": "English",
            "sourcecountry": "United States",
        },
    ]

    df = normalize_articles(raw_articles)
    assert len(df) == 1  # 2 duplicates dropped


def test_source_vs_target_country_decoupling():
    """
    Requirement 2: Strictly decouple publisher origin from mentioned conflict zone.
    Never silently default target country to source country.
    """
    # Case 1: UK outlet reporting on Ukraine conflict
    target_ukr, conf_ukr = resolve_target_country("Heavy missile strikes hit Kyiv infrastructure")
    assert target_ukr == "UKR"
    assert conf_ukr >= 0.75
    source_uk = resolve_source_country("United Kingdom")
    assert source_uk == "GBR"
    assert target_ukr != source_uk  # Decoupled!

    # Case 2: Article with no country entity mentioned
    target_none, conf_none = resolve_target_country("Global technology markets experience major rally")
    assert target_none is None
    assert conf_none == 0.0

    # Case 3: Demonym match (Sudanese -> SDN)
    target_sdn, conf_sdn = resolve_target_country("Sudanese army advances in key border region")
    assert target_sdn == "SDN"
    assert conf_sdn >= 0.75


def test_conflict_taxonomy_classification():
    """Verify rule-based 9-category taxonomy classification."""
    # Armed conflict + military escalation
    title_1 = "Artillery shelling and troop buildup along frontline positions"
    rel_1, counts_1, total_1, prim_1 = classify_conflict_relevance(title_1)
    assert rel_1 is True
    assert counts_1["armed_conflict"] > 0
    assert counts_1["military_escalation"] > 0

    # Ceasefire and peace
    title_2 = "Factions agree to immediate ceasefire and humanitarian truce"
    rel_2, counts_2, total_2, prim_2 = classify_conflict_relevance(title_2)
    assert rel_2 is True
    assert counts_2["ceasefire_peace"] > 0

    # Sanctions
    title_3 = "New trade restrictions and asset freeze sanctions announced"
    rel_3, counts_3, total_3, prim_3 = classify_conflict_relevance(title_3)
    assert rel_3 is True
    assert counts_3["sanctions_economic"] > 0

    # Non-conflict title
    title_non = "City announces new public transport electric bus fleet"
    rel_non, counts_non, total_non, prim_non = classify_conflict_relevance(title_non)
    assert rel_non is False
    assert total_non == 0
    assert prim_non == "none"


def test_deterministic_lexical_tone():
    """Verify continuous lexical tone scoring in [-1.0, 1.0]."""
    # Negative conflict headline
    score_neg, is_neg, is_ext_neg = compute_lexical_tone(
        "Deadly attack kills dozens in terror massacre"
    )
    assert score_neg < -0.4
    assert is_neg is True

    # Positive peace headline
    score_pos, is_pos_neg, is_ext_pos = compute_lexical_tone(
        "Historic peace treaty brings ceasefire, relief, and cooperation"
    )
    assert score_pos > 0.4
    assert is_pos_neg is False

    # Neutral headline
    score_neu, is_neu_neg, is_ext_neu = compute_lexical_tone(
        "Weather forecast indicates seasonal temperatures"
    )
    assert score_neu == 0.0
    assert is_neu_neg is False


def test_safe_relative_growth_division_safety():
    """Verify safe growth rate calculation handles 0-to-positive and zero-division."""
    curr = pd.Series([0.0, 10.0, 5.0, 0.0])
    prev = pd.Series([0.0, 0.0, 10.0, 5.0])
    growth = safe_relative_growth(curr, prev)

    assert not np.isinf(growth).any()
    assert not growth.isna().any()
    assert growth.iloc[0] == 0.0
    assert growth.iloc[1] > 0.0
    assert growth.iloc[2] == -0.5


def test_zero_future_data_leakage():
    """
    Requirement 4: Features at month t must use only information available before or at t.
    Appending articles in month t+1 must NOT alter features at month t.
    """
    base_articles = [
        {
            "article_id": "art1",
            "published_at_utc": pd.Timestamp("2026-06-10", tz=timezone.utc),
            "year_month": "2026-06",
            "target_country_iso3": "UKR",
            "domain": "reuters.com",
            "is_conflict_relevant": True,
            "tone_score": -0.6,
            "is_negative_tone": True,
            "is_extreme_tone": True,
            "cat_military_escalation": True,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
        {
            "article_id": "art2",
            "published_at_utc": pd.Timestamp("2026-07-15", tz=timezone.utc),
            "year_month": "2026-07",
            "target_country_iso3": "UKR",
            "domain": "bbc.com",
            "is_conflict_relevant": True,
            "tone_score": -0.4,
            "is_negative_tone": True,
            "is_extreme_tone": False,
            "cat_military_escalation": False,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
    ]

    panel_1 = aggregate_country_month_news(pd.DataFrame(base_articles))
    feat_1 = compute_time_aware_news_features(panel_1)

    row_jun_1 = feat_1[(feat_1["country_iso3"] == "UKR") & (feat_1["year_month"] == "2026-06")].iloc[0]
    row_jul_1 = feat_1[(feat_1["country_iso3"] == "UKR") & (feat_1["year_month"] == "2026-07")].iloc[0]

    # Future article in August 2026
    future_articles = base_articles + [
        {
            "article_id": "art3",
            "published_at_utc": pd.Timestamp("2026-08-20", tz=timezone.utc),
            "year_month": "2026-08",
            "target_country_iso3": "UKR",
            "domain": "apnews.com",
            "is_conflict_relevant": True,
            "tone_score": -0.9,
            "is_negative_tone": True,
            "is_extreme_tone": True,
            "cat_military_escalation": True,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        }
    ]

    panel_2 = aggregate_country_month_news(pd.DataFrame(future_articles))
    feat_2 = compute_time_aware_news_features(panel_2)

    row_jun_2 = feat_2[(feat_2["country_iso3"] == "UKR") & (feat_2["year_month"] == "2026-06")].iloc[0]
    row_jul_2 = feat_2[(feat_2["country_iso3"] == "UKR") & (feat_2["year_month"] == "2026-07")].iloc[0]

    # Prior features for June and July must be completely unchanged
    check_cols = [
        c for c in feat_1.columns
        if any(k in c for k in ["lag", "prior", "conflict_news", "avg_tone"])
    ]
    for col in check_cols:
        val1 = row_jun_1[col]
        val2 = row_jun_2[col]
        if pd.isna(val1):
            assert pd.isna(val2), f"Leakage detected in June for {col}: {val1} != {val2}"
        else:
            assert val1 == val2, f"Leakage detected in June for {col}: {val1} != {val2}"

        val_jul1 = row_jul_1[col]
        val_jul2 = row_jul_2[col]
        if pd.isna(val_jul1):
            assert pd.isna(val_jul2), f"Leakage detected in July for {col}: {val_jul1} != {val_jul2}"
        else:
            assert val_jul1 == val_jul2, f"Leakage detected in July for {col}: {val_jul1} != {val_jul2}"


def test_unavailable_lag_and_rolling_nan_preservation():
    """
    Requirement: Unobserved history must evaluate to NaN, never silently converted to 0.
    """
    articles = [
        {
            "article_id": "art_sdn_1",
            "published_at_utc": pd.Timestamp("2026-07-15 10:00:00", tz=timezone.utc),
            "year_month": "2026-07",
            "target_country_iso3": "SDN",
            "domain": "reuters.com",
            "is_conflict_relevant": True,
            "tone_score": -0.7,
            "is_negative_tone": True,
            "is_extreme_tone": True,
            "cat_military_escalation": True,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
        {
            "article_id": "art_sdn_2",
            "published_at_utc": pd.Timestamp("2026-08-10 12:00:00", tz=timezone.utc),
            "year_month": "2026-08",
            "target_country_iso3": "SDN",
            "domain": "aljazeera.com",
            "is_conflict_relevant": True,
            "tone_score": -0.5,
            "is_negative_tone": True,
            "is_extreme_tone": False,
            "cat_military_escalation": False,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
    ]

    panel = aggregate_country_month_news(pd.DataFrame(articles))
    feat = compute_time_aware_news_features(panel)

    sdn_jul = feat[(feat["country_iso3"] == "SDN") & (feat["year_month"] == "2026-07")].iloc[0]
    sdn_aug = feat[(feat["country_iso3"] == "SDN") & (feat["year_month"] == "2026-08")].iloc[0]

    # For the earliest observed month (July 2026), lag_1m is outside observation window -> MUST BE NaN
    assert pd.isna(sdn_jul["conflict_news_lag_1m"])
    # 6m and 12m lags are outside observation window -> MUST BE NaN
    assert pd.isna(sdn_jul["conflict_news_lag_6m"])
    assert pd.isna(sdn_aug["conflict_news_lag_6m"])
    assert pd.isna(sdn_jul["conflict_news_lag_12m"])
    assert pd.isna(sdn_aug["conflict_news_lag_12m"])

    # Prior rolling 3m requires 3 completed prior months -> MUST BE NaN in a 2-month dataset
    assert pd.isna(sdn_jul["conflict_news_prior_sum_3m"])
    assert pd.isna(sdn_aug["conflict_news_prior_sum_3m"])


def test_genuine_observed_zero_news_preserved():
    """
    Requirement: A genuine observed month with zero articles must evaluate to 0,
    clearly distinguished from unobserved history.
    """
    articles = [
        # Country has events in July 2026 and September 2026, but ZERO events in August 2026
        {
            "article_id": "art_1",
            "published_at_utc": pd.Timestamp("2026-07-20", tz=timezone.utc),
            "year_month": "2026-07",
            "target_country_iso3": "COL",
            "domain": "eltiempo.com",
            "is_conflict_relevant": True,
            "tone_score": -0.4,
            "is_negative_tone": True,
            "is_extreme_tone": False,
            "cat_military_escalation": False,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
        {
            "article_id": "art_2",
            "published_at_utc": pd.Timestamp("2026-09-15", tz=timezone.utc),
            "year_month": "2026-09",
            "target_country_iso3": "COL",
            "domain": "eltiempo.com",
            "is_conflict_relevant": True,
            "tone_score": -0.6,
            "is_negative_tone": True,
            "is_extreme_tone": True,
            "cat_military_escalation": True,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
    ]

    panel = aggregate_country_month_news(pd.DataFrame(articles))
    feat = compute_time_aware_news_features(panel)

    col_aug = feat[(feat["country_iso3"] == "COL") & (feat["year_month"] == "2026-08")].iloc[0]
    col_sep = feat[(feat["country_iso3"] == "COL") & (feat["year_month"] == "2026-09")].iloc[0]

    # August was an observed month with genuine 0 news
    assert col_aug["news_count_total"] == 0
    assert col_aug["conflict_news_count"] == 0
    assert col_aug["avg_tone"] == 0.0

    # In September, lag_1m looks back at August (genuine 0 news observed!) -> MUST BE 0.0, NOT NaN
    assert col_sep["conflict_news_lag_1m"] == 0.0

    # In August, lag_1m looks back at July (genuine 1 event observed!) -> MUST BE 1.0
    assert col_aug["conflict_news_lag_1m"] == 1.0


def test_partial_month_detection():
    """
    Requirement: Dynamic partial month detection based on actual observation timestamps.
    """
    articles = [
        # Coverage begins July 14, 2026 and ends October 2, 2026
        {
            "article_id": "art_start",
            "published_at_utc": pd.Timestamp("2026-07-14 23:45:00", tz=timezone.utc),
            "year_month": "2026-07",
            "target_country_iso3": "UKR",
            "domain": "bbc.com",
            "is_conflict_relevant": True,
            "tone_score": -0.5,
            "is_negative_tone": True,
            "is_extreme_tone": False,
            "cat_military_escalation": False,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
        {
            "article_id": "art_end",
            "published_at_utc": pd.Timestamp("2026-10-02 08:15:00", tz=timezone.utc),
            "year_month": "2026-10",
            "target_country_iso3": "UKR",
            "domain": "reuters.com",
            "is_conflict_relevant": True,
            "tone_score": -0.8,
            "is_negative_tone": True,
            "is_extreme_tone": True,
            "cat_military_escalation": True,
            "cat_armed_conflict": True,
            "cat_ceasefire_peace": False,
            "cat_sanctions_economic": False,
        },
    ]

    panel = aggregate_country_month_news(pd.DataFrame(articles))

    # July 2026 starts July 14 -> is_partial_month == True
    jul_row = panel[panel["year_month"] == "2026-07"].iloc[0]
    assert bool(jul_row["is_partial_month"]) is True

    # August and September are complete interior months -> is_partial_month == False
    aug_row = panel[panel["year_month"] == "2026-08"].iloc[0]
    assert bool(aug_row["is_partial_month"]) is False

    sep_row = panel[panel["year_month"] == "2026-09"].iloc[0]
    assert bool(sep_row["is_partial_month"]) is False

    # October 2026 ends October 2 -> is_partial_month == True
    oct_row = panel[panel["year_month"] == "2026-10"].iloc[0]
    assert bool(oct_row["is_partial_month"]) is True
