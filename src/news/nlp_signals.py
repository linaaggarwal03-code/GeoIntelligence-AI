"""
Deterministic Lexical NLP Signals Module.
Computes article-level continuous tone, negative/extreme tone flags, and conflict intensity
using transparent lexical dictionaries. Saves clean normalized articles to Parquet.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from src.news.config import (
    PROCESSED_NEWS_DIR,
    PROCESSED_ARTICLES_FILENAME,
    LEXICAL_SENTIMENT_DICT,
)
from src.news.normalize import normalize_articles
from src.news.conflict_classifier import apply_conflict_classification

logger = logging.getLogger(__name__)


def compute_lexical_tone(title: str) -> Tuple[float, bool, bool]:
    """
    Compute continuous tone score in [-1.0, 1.0] from headline words using the
    deterministic lexical dictionary.

    Returns:
    - tone_score (float in [-1.0, 1.0], 0.0 is neutral)
    - is_negative_tone (bool: tone < -0.2)
    - is_extreme_tone (bool: |tone| >= 0.6)
    """
    if not title or not isinstance(title, str):
        return 0.0, False, False

    words = re.findall(r"\b[a-z\-]+\b", title.lower())
    if not words:
        return 0.0, False, False

    sentiment_weights = [LEXICAL_SENTIMENT_DICT[w] for w in words if w in LEXICAL_SENTIMENT_DICT]
    if not sentiment_weights:
        return 0.0, False, False

    # Average sentiment bounded between -1.0 and 1.0
    avg_score = float(np.mean(sentiment_weights))
    avg_score = max(-1.0, min(1.0, avg_score))

    is_negative = avg_score < -0.2
    is_extreme = abs(avg_score) >= 0.6

    return avg_score, is_negative, is_extreme


def enrich_article_nlp_signals(
    df: pd.DataFrame,
    output_parquet_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Add lexical sentiment and intensity scores to the normalized news DataFrame,
    and save clean article dataset to Parquet.
    """
    if df.empty:
        return df

    out_path = output_parquet_path or (PROCESSED_NEWS_DIR / PROCESSED_ARTICLES_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Computing lexical sentiment tone for %d articles...", len(df))
    tone_results = df["title"].apply(compute_lexical_tone)

    df["tone_score"] = [r[0] for r in tone_results]
    df["is_negative_tone"] = [r[1] for r in tone_results]
    df["is_extreme_tone"] = [r[2] for r in tone_results]

    # Conflict intensity score: conflict category count normalized by word count
    word_counts = df["title"].apply(lambda t: len(str(t).split())).clip(lower=1)
    df["conflict_intensity"] = (df["conflict_category_count"] / word_counts).clip(upper=1.0)

    # Save to Parquet
    df.to_parquet(out_path, index=False, engine="pyarrow", compression="snappy")
    logger.info("Saved %d clean article records to %s", len(df), out_path)
    return df
