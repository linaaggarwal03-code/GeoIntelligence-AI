"""
Explainable Rule-Based Conflict Relevance Classification.
Evaluates article titles against a transparent 9-category geopolitical conflict taxonomy.
Provides granular category flags, relevance indicators, and category counts without
black-box model assumptions.
"""

import logging
import re
from typing import Dict, List, Tuple

import pandas as pd

from src.news.config import CONFLICT_TAXONOMY

logger = logging.getLogger(__name__)


def classify_conflict_relevance(title: str) -> Tuple[bool, Dict[str, int], int, str]:
    """
    Classify a headline across the 9 conflict categories.
    Returns:
    - is_conflict_relevant (bool)
    - category_counts (Dict[str, int])
    - total_category_hits (int)
    - primary_category (str)
    """
    if not title or not isinstance(title, str):
        empty_counts = {cat: 0 for cat in CONFLICT_TAXONOMY}
        return False, empty_counts, 0, "none"

    lower_title = title.lower()
    cat_counts: Dict[str, int] = {}
    total_hits = 0

    for category, keywords in CONFLICT_TAXONOMY.items():
        hits = 0
        for kw in keywords:
            # Word boundary regex to avoid partial substring matching (e.g. 'war' in 'wardrobe')
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, lower_title):
                hits += 1
        cat_counts[category] = hits
        total_hits += hits

    is_relevant = total_hits > 0
    # Determine primary category with highest trigger count
    if is_relevant:
        primary_cat = max(cat_counts.items(), key=lambda x: x[1])[0]
    else:
        primary_cat = "none"

    return is_relevant, cat_counts, total_hits, primary_cat


def apply_conflict_classification(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply conflict classification across all records in the DataFrame.
    Appends is_conflict_relevant, conflict_category_count, primary_category,
    and individual Boolean flags (cat_armed_conflict, cat_military_escalation, etc.).
    """
    if df.empty:
        return df

    results = df["title"].apply(classify_conflict_relevance)

    df["is_conflict_relevant"] = [r[0] for r in results]
    df["conflict_category_count"] = [r[2] for r in results]
    df["primary_conflict_category"] = [r[3] for r in results]

    # Add Boolean indicator for each individual taxonomy dimension
    for category in CONFLICT_TAXONOMY:
        df[f"cat_{category}"] = [r[1].get(category, 0) > 0 for r in results]

    relevant_count = df["is_conflict_relevant"].sum()
    logger.info(
        "Conflict classification: %d of %d articles (%.1f%%) classified as conflict-relevant.",
        relevant_count,
        len(df),
        (relevant_count / max(len(df), 1)) * 100,
    )
    return df
