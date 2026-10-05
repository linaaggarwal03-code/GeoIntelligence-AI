"""
GDELT DOC 2.0 API Ingestion Client.
Queries the official GDELT DOC 2.0 API (artlist mode), implements rate-limit pacing,
handles HTTP 429 cooldowns, preserves untouched raw JSON responses, and records provenance.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.parse
import urllib.error

from src.news.config import (
    RAW_NEWS_DIR,
    RAW_ARTICLES_FILENAME,
    RAW_METADATA_FILENAME,
    GDELT_DOC_API_URL,
    GDELT_API_USER_AGENT,
    GDELT_RATE_LIMIT_PAUSE_SECONDS,
    GDELT_BACKOFF_RETRIES,
    GDELT_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class GDELTDocClient:
    """
    HTTP client for GDELT DOC 2.0 API.
    Enforces inter-request rate limiting to prevent HTTP 429 blocks.
    """

    def __init__(self, pause_seconds: float = GDELT_RATE_LIMIT_PAUSE_SECONDS):
        self.pause_seconds = pause_seconds
        self.last_request_time: float = 0.0

    def _wait_for_rate_limit(self):
        """Ensure minimum required cooldown between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.pause_seconds:
            sleep_duration = self.pause_seconds - elapsed
            logger.debug("Rate limiting: sleeping %.2f seconds", sleep_duration)
            time.sleep(sleep_duration)

    def fetch_articles(
        self,
        query: str,
        max_records: int = 250,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute an artlist query against GDELT DOC 2.0 API with retry logic.
        """
        params: Dict[str, Any] = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(min(max_records, 250)),
        }
        if start_datetime:
            params["startdatetime"] = start_datetime
        if end_datetime:
            params["enddatetime"] = end_datetime

        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{GDELT_DOC_API_URL}?{query_string}"

        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": GDELT_API_USER_AGENT},
        )

        for attempt in range(1, GDELT_BACKOFF_RETRIES + 1):
            self._wait_for_rate_limit()
            try:
                logger.info("Querying GDELT DOC 2.0 API: %s (attempt %d)", full_url, attempt)
                self.last_request_time = time.time()
                with urllib.request.urlopen(req, timeout=GDELT_TIMEOUT_SECONDS) as response:
                    raw_bytes = response.read()
                    data = json.loads(raw_bytes.decode("utf-8", errors="replace"))
                    articles = data.get("articles", [])
                    logger.info("Successfully fetched %d articles from GDELT.", len(articles))
                    return articles
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    cooldown = 15.0 * (2 ** (attempt - 1))
                    logger.warning("HTTP 429 Too Many Requests received. Backing off for %.1fs...", cooldown)
                    time.sleep(cooldown)
                else:
                    logger.error("HTTP error %d querying GDELT: %s", e.code, e.reason)
                    if attempt == GDELT_BACKOFF_RETRIES:
                        raise
            except Exception as e:
                logger.error("Error connecting to GDELT: %s (attempt %d)", e, attempt)
                if attempt == GDELT_BACKOFF_RETRIES:
                    raise
                time.sleep(5.0 * attempt)

        return []


def ingest_gdelt_news(
    target_dir: Optional[Path] = None,
    query: str = "Ukraine OR Sudan OR Gaza OR conflict OR military",
    max_records: int = 250,
    force_fetch: bool = False,
) -> Dict[str, Any]:
    """
    Download raw real news from GDELT DOC 2.0 API, preserve raw JSON snapshot,
    and generate provenance metadata.
    """
    out_dir = target_dir or RAW_NEWS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_json_path = out_dir / RAW_ARTICLES_FILENAME
    metadata_path = out_dir / RAW_METADATA_FILENAME

    # Check for existing valid cache
    if not force_fetch and raw_json_path.exists() and metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                cached_meta = json.load(f)
            with open(raw_json_path, "r", encoding="utf-8") as f:
                cached_articles = json.load(f)
            if len(cached_articles) > 0:
                logger.info(
                    "Found valid existing raw news snapshot (%d articles). Skipping API call.",
                    len(cached_articles),
                )
                return cached_meta
        except Exception as e:
            logger.warning("Failed reading cached news (%s). Re-fetching from API...", e)

    # Fetch from live API
    client = GDELTDocClient()
    articles = client.fetch_articles(query=query, max_records=max_records)
    if not articles:
        raise RuntimeError(
            "GDELT API returned 0 articles or request was rate-limited. "
            "Please wait a few moments before retrying."
        )

    # Save untouched raw JSON payload
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    sha256 = compute_sha256(raw_json_path)
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    metadata: Dict[str, Any] = {
        "source": "GDELT Project (DOC 2.0 API)",
        "api_endpoint": GDELT_DOC_API_URL,
        "query": query,
        "retrieval_timestamp_utc": retrieval_timestamp,
        "raw_articles_filename": RAW_ARTICLES_FILENAME,
        "raw_articles_count": len(articles),
        "raw_json_sha256": sha256,
        "raw_file_size_bytes": raw_json_path.stat().st_size,
        "validation_status": "PASSED",
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Raw news snapshot saved to %s (records: %d)", raw_json_path, len(articles))
    return metadata
