import json
import logging
import os
from pathlib import Path

import boto3
import psycopg

from ingest_tsma_excel_folder import insert_tsma_workbook
from ingest_raw_excel_folder import (
    insert_telus_workbook,
    insert_rogers_cellular_workbook,
    insert_rogers_voice_workbook,
)
from ingest_tsma_other_excel_folder import insert_workbook as insert_tsma_other_workbook

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

_cached_dsn: str | None = None


def _get_dsn() -> str:
    global _cached_dsn
    if _cached_dsn:
        return _cached_dsn
    host = os.environ["DB_HOST"]
    password = os.environ["DB_PASSWORD"]
    user = os.environ.get("DB_USER", "dbadmin")
    name = os.environ.get("DB_NAME", "app")
    _cached_dsn = f"postgresql://{user}:{password}@{host}:5432/{name}"
    return _cached_dsn


def _download(bucket: str, key: str) -> Path:
    tmp_path = Path(f"/tmp/{key.split('/')[-1]}")
    logger.info("Downloading s3://%s/%s", bucket, key)
    s3_client.download_file(bucket, key, str(tmp_path))
    return tmp_path


# ---------------------------------------------------------------------------
# Feed handlers — one per ingestion script
# S3 key conventions mirror the local folder layout each script expects:
#
#   tsma/wireless/          → tsma_wireless
#   tsma/wireline/          → tsma_wireline
#   tsma/master/            → tsma_master
#   tsma_lite/wireless/     → tsma_lite_wireless
#   tsma_lite/wireline/     → tsma_lite_wireline
#
#   ngta/telus/             → ngta telus spend
#   ngta/rogers/cellular/   → ngta rogers cellular
#   ngta/rogers/voice/      → ngta rogers voice
#
#   tsma_other/managed_security/ → tsma_other_managed_security
#   tsma_other/managed_router/   → tsma_other_managed_router
# ---------------------------------------------------------------------------

def _handle_tsma(bucket: str, key: str) -> None:
    feed_map = {
        ("tsma",      "wireless"): "tsma_wireless",
        ("tsma",      "wireline"): "tsma_wireline",
        ("tsma",      "master"):   "tsma_master",
        ("tsma_lite", "wireless"): "tsma_lite_wireless",
        ("tsma_lite", "wireline"): "tsma_lite_wireline",
    }
    parts = [p.casefold() for p in key.split("/")]
    feed = next(
        (v for (a, b), v in feed_map.items() if a in parts and b in parts),
        None,
    )
    if not feed:
        logger.info("Unrecognised TSMA key structure, skipping: %s", key)
        return

    tmp_path = _download(bucket, key)
    try:
        with psycopg.connect(_get_dsn()) as conn:
            counts = insert_tsma_workbook(
                conn=conn, path=tmp_path, feed=feed,
                source_period=None, dry_run=False, sheet=None,
            )
        logger.info("Ingested %s feed=%s counts=%s", key, feed, counts)
    finally:
        tmp_path.unlink(missing_ok=True)


def _handle_ngta_telus(bucket: str, key: str) -> None:
    tmp_path = _download(bucket, key)
    try:
        with psycopg.connect(_get_dsn()) as conn:
            n = insert_telus_workbook(
                conn=conn, path=tmp_path, source_period=None, dry_run=False,
            )
        logger.info("Ingested %s rows from %s (NGTA Telus)", n, key)
    finally:
        tmp_path.unlink(missing_ok=True)


def _handle_ngta_rogers(bucket: str, key: str) -> None:
    parts = [p.casefold() for p in key.split("/")]
    is_cellular = "cellular" in parts
    is_voice = "voice" in parts or "data" in parts

    tmp_path = _download(bucket, key)
    try:
        with psycopg.connect(_get_dsn()) as conn:
            if is_cellular:
                n = insert_rogers_cellular_workbook(
                    conn=conn, path=tmp_path, source_period=None, dry_run=False, sheet=None,
                )
            elif is_voice:
                n = insert_rogers_voice_workbook(
                    conn=conn, path=tmp_path, source_period=None, dry_run=False, sheet=None,
                )
            else:
                logger.info("Cannot determine Rogers feed type from key: %s", key)
                return
        logger.info("Ingested %s rows from %s (NGTA Rogers)", n, key)
    finally:
        tmp_path.unlink(missing_ok=True)


def _handle_tsma_other(bucket: str, key: str) -> None:
    feed_map = {
        "managed_security": "tsma_other_managed_security",
        "managed_router":   "tsma_other_managed_router",
    }
    parts = [p.casefold() for p in key.split("/")]
    feed = next((v for k, v in feed_map.items() if k in parts), None)
    if not feed:
        logger.info("Unrecognised TSMA Other key structure, skipping: %s", key)
        return

    tmp_path = _download(bucket, key)
    try:
        with psycopg.connect(_get_dsn()) as conn:
            n = insert_tsma_other_workbook(
                conn=conn, path=tmp_path, feed=feed,
                source_period=None, dry_run=False, sheet=None,
            )
        logger.info("Ingested %s rows from %s (TSMA Other %s)", n, key, feed)
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Router — maps S3 key prefix to handler
# ---------------------------------------------------------------------------

_ROUTES = [
    ("tsma/",                   _handle_tsma),
    ("tsma_lite/",              _handle_tsma),
    ("tsma_other/",             _handle_tsma_other),
    ("ngta/telus/",             _handle_ngta_telus),
    ("ngta/rogers/",            _handle_ngta_rogers),
]


# ---------------------------------------------------------------------------
# Lambda entrypoint
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    logger.info("Event: %s", json.dumps(event))

    dry_run = os.environ.get("DRY_RUN", "").lower() == "true"

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"].replace("+", " ")

        handler = next((h for prefix, h in _ROUTES if key.startswith(prefix)), None)
        if handler is None:
            logger.info("No handler registered for key: %s", key)
            continue

        if dry_run:
            logger.info("DRY_RUN enabled — skipping ingest for s3://%s/%s", bucket, key)
            continue

        handler(bucket, key)

    return {"statusCode": 200, "body": "OK"}
