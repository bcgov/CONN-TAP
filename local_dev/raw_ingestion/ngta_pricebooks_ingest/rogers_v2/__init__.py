"""Rogers NGTA pricebook v2 ingestion (new single-sheet RCCI workbook format)."""

from .ingest import process_file

__all__ = ["process_file"]
