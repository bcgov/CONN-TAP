"""Telus NGTA pricebook v2 workbook/sheet -> raw Postgres table mapping.

The v2 price books arrive as a single multi-sheet workbook per book (e.g.
"TCI NGTA Price Book Cellular Services v2.0.xlsx") instead of the old
one-file-per-catalogue u_ngta_*.xlsx layout, so routing is by (book, sheet
name) rather than by filename stem alone.

Most sheets are a plain header-row-plus-data-rows table (SimpleSheetSpec).
A few sheets pack several catalogues into one sheet with repeating header
rows (e.g. Stadium vs Pooled rate plans on "TELUS Control Center Service");
those are handled by a dedicated parser function named in MultiBlockSheetSpec
(see telus_v2/excel.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimpleSheetSpec:
    sheet_name: str
    table_name: str
    columns: tuple[str, ...]
    feed_code: str
    header_row: int = 1  # 1-indexed Excel row holding column headers
    # Literal values stamped onto every row parsed from this sheet, e.g.
    # {"type_of_service": "Basic Fee-Based Features"} when several sheets
    # share one table_name (mirrors the old schema, where a single table
    # held several groups distinguished only by type_of_service).
    literal_columns: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MultiBlockSheetSpec:
    sheet_name: str
    table_name: str
    columns: tuple[str, ...]
    feed_code: str
    parser: str  # key into telus_v2.excel.MULTI_BLOCK_PARSERS


SheetSpec = SimpleSheetSpec | MultiBlockSheetSpec


@dataclass(frozen=True)
class BookSpec:
    book_code: str
    file_match: str  # lowercase substring matched against the file stem
    sheets: tuple[SheetSpec, ...]


CELLULAR_SERVICES_V2 = BookSpec(
    book_code="cellular_services_v2",
    file_match="cellular services",
    sheets=(
        # These three sheets share one table, mirroring the old
        # raw_telus_cellular_services_pricebook: the old
        # u_ngta_cellular_services_catalogue.xlsx was itself a single file
        # covering all three groups, distinguished only by type_of_service
        # ('Cellular Services' / 'Basic Fee-Based Features' / 'Advanced
        # Fee-Based features') — confirmed against the real old file.
        SimpleSheetSpec(
            sheet_name="Cellular Services",
            table_name="raw_telus_v2_cellular_services_pricebook",
            columns=("category", "rate_plan", "service_id", "monthly_fee", "type_of_service"),
            feed_code="cellular_services",
            literal_columns={"type_of_service": "Cellular Services"},
        ),
        SimpleSheetSpec(
            sheet_name="Basic Fee-Based Features",
            table_name="raw_telus_v2_cellular_services_pricebook",
            columns=("category", "rate_plan", "service_id", "monthly_fee", "type_of_service"),
            feed_code="cellular_basic_fee_based_features",
            literal_columns={"type_of_service": "Basic Fee-Based Features"},
        ),
        SimpleSheetSpec(
            sheet_name="Advanced Fee-Based features",
            table_name="raw_telus_v2_cellular_services_pricebook",
            columns=("category", "rate_plan", "service_id", "monthly_fee", "type_of_service"),
            feed_code="cellular_advanced_fee_based_features",
            literal_columns={"type_of_service": "Advanced Fee-Based features"},
        ),
        # type_of_service was a constant in each of these four old files
        # (confirmed against the real old files) — carried forward here as a
        # hardcoded literal, same technique as the cellular_services group
        # above, since the new sheets don't repeat that column themselves.
        SimpleSheetSpec(
            sheet_name="Additional Fee-Based Features",
            table_name="raw_telus_v2_cellular_additional_fee_based_features_pricebook",
            columns=("service", "service_id", "fee", "cpm_rate", "type_of_service"),
            feed_code="cellular_additional_fee_based_features",
            literal_columns={"type_of_service": "Additional Fee-Based Features"},
        ),
        SimpleSheetSpec(
            sheet_name="Roaming",
            table_name="raw_telus_v2_cellular_roaming_pricebook",
            columns=("roaming", "fee", "type_of_service"),
            feed_code="cellular_roaming",
            literal_columns={"type_of_service": "Roaming"},
        ),
        SimpleSheetSpec(
            sheet_name="Long Distance",
            table_name="raw_telus_v2_cellular_long_distance_pricebook",
            columns=("calling_to", "cpm_rate", "type_of_service"),
            feed_code="cellular_long_distance",
            literal_columns={"type_of_service": "Long Distance"},
        ),
        SimpleSheetSpec(
            sheet_name="Managed Mobility Services (MMS)",
            table_name="raw_telus_v2_cellular_mms_pricebook",
            columns=("service", "service_id", "monthly_fee", "incident_cap", "type_of_service"),
            feed_code="cellular_mms",
            literal_columns={"type_of_service": "MMS"},
        ),
        SimpleSheetSpec(
            sheet_name="GINGER Management Services GMS",
            table_name="raw_telus_v2_gms_pricebook",
            columns=("service", "service_id", "monthly_fee"),
            feed_code="gms",
        ),
        SimpleSheetSpec(
            sheet_name="GMS Usage Rate",
            table_name="raw_telus_v2_gms_usage_rate_pricebook",
            columns=("service", "usage_rate", "detail"),
            feed_code="gms_usage_rate",
        ),
        MultiBlockSheetSpec(
            sheet_name="TELUS Control Center Service",
            table_name="raw_telus_v2_control_center_pricebook",
            columns=(
                "section",
                "category",
                "item_description",
                "service_id",
                "monthly_fee",
                "overage_charges",
                "fee_type",
            ),
            feed_code="control_center",
            parser="control_center",
        ),
        MultiBlockSheetSpec(
            sheet_name="Fleet Complete Services",
            table_name="raw_telus_v2_fleet_complete_pricebook",
            columns=("section", "item", "description", "code", "price"),
            feed_code="fleet_complete",
            parser="fleet_complete",
        ),
        MultiBlockSheetSpec(
            sheet_name="Connected Worker Solution",
            table_name="raw_telus_v2_connected_worker_pricebook",
            columns=(
                "section",
                "item",
                "description",
                "service_id",
                "monthly_fee",
                "dependencies",
            ),
            feed_code="connected_worker",
            parser="connected_worker",
        ),
        SimpleSheetSpec(
            sheet_name="Connected Worker CPM Usage Rate",
            table_name="raw_telus_v2_connected_worker_usage_rate_pricebook",
            columns=("item", "description", "service_id", "usage_rate"),
            feed_code="connected_worker_usage_rate",
            header_row=4,
        ),
    ),
)

CELLULAR_DEVICES_V2 = BookSpec(
    book_code="cellular_devices_catalogue_v2",
    file_match="devices catalogue",
    sheets=(
        # Mirrors the old raw_telus_cellular_device_pricebook exactly (same
        # columns; type_of_service was a constant 'Device Catalogue' in the
        # old file, confirmed against the real old source file).
        SimpleSheetSpec(
            sheet_name="Cellular Devices Catalogue",
            table_name="raw_telus_v2_cellular_device_pricebook",
            columns=("device_name", "device_price", "type_of_service"),
            feed_code="cellular_device",
            literal_columns={"type_of_service": "Device Catalogue"},
        ),
        # New catalogue, no old precedent: wearable/satellite hardware and
        # accessories supporting the Connected Worker Solution sheet from
        # the Cellular Services v2.0 book.
        SimpleSheetSpec(
            sheet_name="Connected Worker Hardware",
            table_name="raw_telus_v2_connected_worker_hardware_pricebook",
            columns=("item", "description", "service_id", "price", "dependencies"),
            feed_code="connected_worker_hardware",
            header_row=5,
        ),
    ),
)

BOOKS: tuple[BookSpec, ...] = (CELLULAR_SERVICES_V2, CELLULAR_DEVICES_V2)


def resolve_book(file_stem: str) -> BookSpec:
    stem = file_stem.casefold()
    for book in BOOKS:
        if book.file_match in stem:
            return book
    known = ", ".join(b.file_match for b in BOOKS)
    raise ValueError(f"Unknown Telus v2 pricebook {file_stem!r}; expected filename containing one of: {known}")


def resolve_sheet(book: BookSpec, sheet_name: str) -> SheetSpec | None:
    target = sheet_name.strip().casefold()
    for spec in book.sheets:
        if spec.sheet_name.strip().casefold() == target:
            return spec
    return None
