"""
News Intelligence and NLP Pipeline Package (Member 3 Milestone 2).
Provides real-world news ingestion from GDELT DOC 2.0 API, country entity mapping,
rule-based conflict taxonomy classification, deterministic lexical sentiment scoring,
and leak-free country-month feature generation.
"""

from src.news.config import (
    RAW_NEWS_DIR,
    PROCESSED_NEWS_DIR,
    PROCESSED_FEATURES_FILENAME,
)

__all__ = [
    "RAW_NEWS_DIR",
    "PROCESSED_NEWS_DIR",
    "PROCESSED_FEATURES_FILENAME",
]
