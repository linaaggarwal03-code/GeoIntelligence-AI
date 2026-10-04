import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("geointelligence.ingestion")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class IngestionError(Exception):
    """Base exception for data ingestion failures."""
    pass


class APIKeyMissingError(IngestionError):
    """Raised when a required external API key is not configured."""
    pass


class APIResponseError(IngestionError):
    """Raised when an external API returns an error status or malformed payload."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class HTTPClient:
    """
    Robust HTTP client with exponential backoff retries, explicit timeouts,
    detailed error logging, and JSON validation.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: tuple = (429, 500, 502, 503, 504),
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """
        Execute an HTTP GET request with retries, timeout, and logging.
        """
        req_timeout = timeout if timeout is not None else self.timeout
        req_headers = headers or {}
        if "User-Agent" not in req_headers:
            req_headers["User-Agent"] = "GeoIntelligence-AI/1.0"

        logger.info(f"Sending GET request to {url} (params: {params})")

        try:
            response = self.session.get(
                url,
                params=params,
                headers=req_headers,
                timeout=req_timeout,
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"Request to {url} timed out after {req_timeout}s: {e}")
            raise APIResponseError(f"Request to {url} timed out after {req_timeout}s") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error requesting {url}: {e}")
            raise APIResponseError(f"Network error requesting {url}: {str(e)}") from e

        if not response.ok:
            error_msg = f"HTTP {response.status_code} received from {url}"
            logger.error(f"{error_msg} | Body: {response.text[:300]}")
            raise APIResponseError(
                message=error_msg,
                status_code=response.status_code,
                response_text=response.text,
            )

        return response

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Union[Dict[str, Any], list]:
        """
        Fetch URL and decode JSON response safely.
        """
        response = self.get(url, params=params, headers=headers, timeout=timeout)
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Malformed JSON returned from {url}: {response.text[:200]}")
            raise APIResponseError(
                f"Malformed JSON returned from {url}",
                status_code=response.status_code,
                response_text=response.text,
            ) from e


def save_raw_json(data: Union[Dict[str, Any], list], file_path: Union[str, Path]) -> Path:
    """
    Saves raw external API response to a deterministic JSON file path,
    ensuring parent directories exist.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw data to {path}")
    return path
