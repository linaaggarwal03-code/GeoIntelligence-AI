"""
News Normalization and Country Entity Resolution Module.
Normalizes timestamps to UTC, computes deterministic article hashes, canonicalizes URLs/domains,
and resolves mentioned countries to ISO 3166-1 alpha-3 standards while strictly decoupling
publisher origin (source_country_iso3) from affected conflict zone (target_country_iso3).
"""

import hashlib
import logging
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.news.config import (
    ENTITY_TO_ISO3,
    GDELT_SOURCE_COUNTRY_TO_ISO3,
)

logger = logging.getLogger(__name__)


def generate_article_id(url: str, title: str) -> str:
    """Generate a deterministic 16-character hex hash from normalized URL and title."""
    norm_url = url.strip().lower()
    norm_title = title.strip().lower()
    content_key = f"{norm_url}::{norm_title}".encode("utf-8")
    return hashlib.sha256(content_key).hexdigest()[:16]


def parse_gdelt_timestamp(seendate_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parse GDELT's 'YYYYMMDDTHHMMSSZ' format into UTC datetime and 'YYYY-MM' period string.
    """
    if not seendate_str or not isinstance(seendate_str, str):
        return None, None
    clean_str = seendate_str.strip()
    try:
        # Standard GDELT format: 20260813T024500Z
        dt = datetime.strptime(clean_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        year_month = dt.strftime("%Y-%m")
        return dt, year_month
    except ValueError:
        pass

    # Fallback to date-only formats if present
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(clean_str, fmt).replace(tzinfo=timezone.utc)
            return dt, dt.strftime("%Y-%m")
        except ValueError:
            continue

    return None, None


def canonicalize_domain(domain_str: str) -> str:
    """Clean and lowercase publisher domain name."""
    if not domain_str:
        return "unknown"
    d = domain_str.strip().lower()
    if d.startswith("www."):
        d = d[4:]
    return d


def resolve_source_country(sourcecountry_str: str) -> Optional[str]:
    """Map GDELT's sourcecountry string to ISO 3166-1 alpha-3."""
    if not sourcecountry_str or not isinstance(sourcecountry_str, str):
        return None
    clean_name = sourcecountry_str.strip().lower()
    return GDELT_SOURCE_COUNTRY_TO_ISO3.get(clean_name)


def resolve_target_country(title: str) -> Tuple[Optional[str], float]:
    """
    Extract the mentioned/affected country entity from the article headline.
    Returns (target_country_iso3, confidence_score).

    Guarantees:
    - Never defaults to publisher source country.
    - Low-confidence or unmentioned titles return (None, 0.0).
    """
    if not title or not isinstance(title, str):
        return None, 0.0

    lower_title = title.lower()
    # Tokenize words for boundary-aware matching
    tokens = set(re.findall(r"\b[a-z\-]+\b", lower_title))

    # 1. Multi-word entity checks first (e.g. 'burkina faso', 'south sudan', 'united states')
    for phrase, iso3 in ENTITY_TO_ISO3.items():
        if " " in phrase and phrase in lower_title:
            return iso3, 0.95

    # 2. Single-word entity matches
    matched_candidates: List[Tuple[str, float]] = []
    for term, iso3 in ENTITY_TO_ISO3.items():
        if " " not in term and term in tokens:
            # Capital cities and country names give high confidence
            confidence = 0.9 if len(term) > 3 else 0.75
            matched_candidates.append((iso3, confidence))

    if matched_candidates:
        # Return candidate with highest confidence
        matched_candidates.sort(key=lambda x: x[1], reverse=True)
        return matched_candidates[0]

    # No reliable target country identified in headline
    return None, 0.0


def normalize_articles(raw_articles: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Normalize raw GDELT records into a clean tabular DataFrame with deduplication,
    UTC timestamps, and decoupled country resolution.
    """
    if not raw_articles:
        logger.warning("Empty raw articles list passed to normalizer.")
        return pd.DataFrame()

    records = []
    for art in raw_articles:
        url = str(art.get("url", "")).strip()
        title = str(art.get("title", "")).strip()
        if not url or not title:
            continue

        article_id = generate_article_id(url, title)
        seendate_raw = str(art.get("seendate", ""))
        published_at, year_month = parse_gdelt_timestamp(seendate_raw)
        if not published_at:
            continue

        domain = canonicalize_domain(str(art.get("domain", "")))
        language = str(art.get("language", "English")).strip()
        raw_sourcecountry = str(art.get("sourcecountry", "")).strip()

        source_country_iso3 = resolve_source_country(raw_sourcecountry)
        target_country_iso3, match_confidence = resolve_target_country(title)

        records.append({
            "article_id": article_id,
            "published_at_utc": published_at,
            "year": published_at.year,
            "month": published_at.month,
            "year_month": year_month,
            "title": title,
            "url": url,
            "domain": domain,
            "language": language,
            "raw_sourcecountry": raw_sourcecountry,
            "source_country_iso3": source_country_iso3,
            "target_country_iso3": target_country_iso3,
            "target_country_confidence": match_confidence,
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Deduplication
    initial_len = len(df)
    # Deduplicate exact article_id
    df = df.drop_duplicates(subset=["article_id"]).copy()

    # Deduplicate same title on same date (syndicated wire mirrors)
    df["date_str"] = df["published_at_utc"].dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates(subset=["date_str", "title"]).copy()
    df = df.drop(columns=["date_str"])

    logger.info(
        "Normalized %d raw articles into %d deduplicated records (%d dropped).",
        initial_len,
        len(df),
        initial_len - len(df),
    )
    return df.reset_index(drop=True)
