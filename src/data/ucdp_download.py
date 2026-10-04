"""
UCDP GED Download and Raw Ingestion Module.
Downloads the official UCDP Georeferenced Event Dataset (GED) v26.1 archive,
verifies zip and CSV integrity, extracts the raw CSV, computes actual row counts,
and records comprehensive provenance metadata.
"""

import hashlib
import json
import logging
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import urllib.request

from src.data.config import (
    RAW_UCDP_DIR,
    RAW_ZIP_FILENAME,
    RAW_CSV_FILENAME,
    RAW_METADATA_FILENAME,
    UCDP_DOWNLOAD_URL,
    UCDP_DATASET_NAME,
    UCDP_DATASET_VERSION,
    UCDP_SOURCE_NAME,
)

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 checksum for a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_csv_records(csv_path: Path) -> int:
    """
    Count the actual number of data rows in the CSV (excluding the header).
    Calculated dynamically from the extracted file using csv.reader to handle multiline fields.
    """
    import csv
    record_count = 0
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # Skip header
        except StopIteration:
            return 0
        for _ in reader:
            record_count += 1
    return record_count


def download_ucdp_ged(
    target_dir: Optional[Path] = None,
    force_download: bool = False,
    timeout_seconds: int = 180,
) -> Dict[str, Any]:
    """
    Download official UCDP GED Global archive, extract raw CSV, and generate metadata.
    
    Validations performed:
    - HTTP response success (status 200)
    - ZIP archive integrity (zipfile.testzip())
    - CSV presence inside the ZIP
    - Actual row count calculation
    - Cryptographic SHA-256 checksums
    """
    out_dir = target_dir or RAW_UCDP_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / RAW_ZIP_FILENAME
    csv_path = out_dir / RAW_CSV_FILENAME
    metadata_path = out_dir / RAW_METADATA_FILENAME

    # Check if existing raw files are already valid
    if not force_download and zip_path.exists() and csv_path.exists() and metadata_path.exists():
        logger.info("Checking existing raw UCDP artifacts at %s", out_dir)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                if zf.testzip() is None and RAW_CSV_FILENAME in zf.namelist():
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        cached_meta = json.load(f)
                    logger.info(
                        "Valid cached raw dataset found (version: %s, records: %d). Skipping download.",
                        cached_meta.get("dataset_version"),
                        cached_meta.get("raw_record_count", 0),
                    )
                    return cached_meta
        except Exception as e:
            logger.warning("Existing cache validation failed (%s). Re-downloading...", e)

    logger.info("Initiating download from: %s", UCDP_DOWNLOAD_URL)
    req = urllib.request.Request(
        UCDP_DOWNLOAD_URL,
        headers={"User-Agent": "GeoIntelligence-AI-Pipeline/1.0"},
    )

    temp_zip_path = out_dir / f"{RAW_ZIP_FILENAME}.tmp"
    start_time = time.time()

    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        status_code = getattr(response, "status", 200)
        if status_code != 200:
            raise RuntimeError(f"HTTP download failed with status {status_code}")

        bytes_written = 0
        chunk_size = 256 * 1024  # 256 KB chunks
        with open(temp_zip_path, "wb") as f_out:
            while chunk := response.read(chunk_size):
                f_out.write(chunk)
                bytes_written += len(chunk)

    elapsed = time.time() - start_time
    logger.info(
        "Downloaded %.2f MB in %.1f seconds (%.2f MB/s)",
        bytes_written / (1024 * 1024),
        elapsed,
        (bytes_written / (1024 * 1024)) / max(elapsed, 0.1),
    )

    # Atomic move
    if zip_path.exists():
        zip_path.unlink()
    temp_zip_path.rename(zip_path)

    # 1. Validate ZIP Integrity
    logger.info("Validating ZIP integrity...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad_file = zf.testzip()
        if bad_file is not None:
            raise ValueError(f"Corrupted file inside downloaded zip: {bad_file}")

        file_list = zf.namelist()
        if RAW_CSV_FILENAME not in file_list:
            # Check case-insensitively or match by prefix
            matched = [fn for fn in file_list if fn.lower().endswith(".csv")]
            if not matched:
                raise FileNotFoundError(
                    f"Expected CSV file '{RAW_CSV_FILENAME}' not found in zip archive: {file_list}"
                )
            target_csv_in_zip = matched[0]
        else:
            target_csv_in_zip = RAW_CSV_FILENAME

        logger.info("Extracting '%s' from zip...", target_csv_in_zip)
        zf.extract(target_csv_in_zip, path=out_dir)

        extracted_file = out_dir / target_csv_in_zip
        if extracted_file != csv_path:
            if csv_path.exists():
                csv_path.unlink()
            extracted_file.rename(csv_path)

    # 2. Compute actual metrics from extracted files
    logger.info("Computing checksums and counting raw records...")
    zip_sha256 = compute_sha256(zip_path)
    csv_sha256 = compute_sha256(csv_path)
    actual_record_count = count_csv_records(csv_path)
    zip_size_bytes = zip_path.stat().st_size
    csv_size_bytes = csv_path.stat().st_size

    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    metadata: Dict[str, Any] = {
        "source": UCDP_SOURCE_NAME,
        "dataset_name": UCDP_DATASET_NAME,
        "dataset_version": UCDP_DATASET_VERSION,
        "retrieval_timestamp_utc": retrieval_timestamp,
        "source_url": UCDP_DOWNLOAD_URL,
        "source_filename": RAW_CSV_FILENAME,
        "raw_zip_filename": RAW_ZIP_FILENAME,
        "raw_zip_size_bytes": zip_size_bytes,
        "raw_zip_sha256": zip_sha256,
        "raw_csv_filename": RAW_CSV_FILENAME,
        "raw_csv_size_bytes": csv_size_bytes,
        "raw_csv_sha256": csv_sha256,
        "raw_record_count": actual_record_count,
        "validation_status": "PASSED",
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(
        "Raw UCDP snapshot ready. Actual records: %d | Zip SHA-256: %s...",
        actual_record_count,
        zip_sha256[:12],
    )
    return metadata
