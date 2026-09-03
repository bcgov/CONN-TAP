"""Telus NGTA pricebook v2 ingestion (new multi-sheet workbook format)."""

from .ingest import process_file

__all__ = ["process_file"]
