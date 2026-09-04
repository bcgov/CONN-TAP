"""Rogers NGTA pricebook v2 workbook/sheet -> raw Postgres table mapping.

RCCI (Rogers Communications Canada Inc.) sent two new price books as
single-sheet Excel workbooks, replacing the old rogers/*.pdf feeds for the
catalogues they cover. Both are plain header-row-plus-data-rows sheets (no
merged cells, no repeating header blocks), so this reuses SimpleSheetSpec
only — no MultiBlockSheetSpec/SplitByValueSheetSpec machinery is needed here
the way telus_v2 needed it.
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
    literal_columns: dict[str, str] = field(default_factory=dict)


SheetSpec = SimpleSheetSpec


@dataclass(frozen=True)
class BookSpec:
    book_code: str
    file_match: str  # lowercase substring matched against the file stem
    sheets: tuple[SheetSpec, ...]


# Mirrors the old raw_rogers_cellular_pricebook exactly (same 11 fields);
# the old table was built from cellular.pdf, this is the same catalogue as
# an Excel workbook instead. Monthly Fixed Fee / RLH overage fees are all
# zeroed in this file — RCCI masked pricing before sending it (confirmed:
# every priced row reads $0.00 / 0), same as several of the Telus v2 books.
CELLULAR_SERVICES_V2 = BookSpec(
    book_code="cellular_v2",
    file_match="cellular services",
    sheets=(
        SimpleSheetSpec(
            sheet_name="Cellular Services",
            table_name="raw_rogers_v2_cellular_pricebook",
            columns=(
                "service_id",
                "service_name",
                "service_component",
                "speed_mbps_or_capacity_mb",
                "monthly_fixed_fee",
                "ecf_rate",
                "rlh_roam_like_home_usa_overage_fee",
                "rlh_roam_like_home_intl_overage_fee",
                "ecf_unit_of_measure",
                "fixed_fee",
                "overage_charge",
            ),
            feed_code="cellular",
        ),
    ),
)

# New catalogue, no old table precedent — Rogers pricebook ingestion never
# had a device catalogue feed before this. Header is row 2 (row 1 is a
# "CONFIDENTIAL Rogers Communications Canada Inc." title banner spanning
# A1:K1). Price is zeroed on every row, same masking as Cellular Services.
CELLULAR_DEVICES_V2 = BookSpec(
    book_code="cellular_devices_catalogue_v2",
    file_match="devices catalogue",
    sheets=(
        SimpleSheetSpec(
            sheet_name="Cellular Devices Catalogue",
            table_name="raw_rogers_v2_cellular_device_pricebook",
            columns=(
                "status",
                "service_id",
                "device_name",
                "type",
                "brand",
                "model",
                "series",
                "trim",
                "capacity",
                "color",
                "price",
            ),
            feed_code="cellular_device",
            header_row=2,
        ),
    ),
)

# Mirrors the old raw_rogers_data_pricebook exactly (same 7 fields); the old
# table was built from data.pdf, this is the same catalogue as an Excel
# workbook instead. Monthly Fixed Fee is zeroed in this file, same masking
# as the Cellular Services book.
DATA_SERVICES_V2 = BookSpec(
    book_code="data_v2",
    file_match="data services",
    sheets=(
        SimpleSheetSpec(
            sheet_name="Data Services",
            table_name="raw_rogers_v2_data_pricebook",
            columns=(
                "service_id",
                "service_name",
                "service_component",
                "speed_mbps_or_capacity_mb",
                "monthly_fixed_fee",
                "ecf_rate",
                "ecf_unit_of_measure",
            ),
            feed_code="data",
        ),
    ),
)

# Mirrors the old raw_rogers_voice_pricebook exactly (same 10 fields,
# including voice_table_section) — the old table was built from voice.pdf's
# two tables (base_service pp.1-2, long_distance), and this workbook sends
# the same two tables as two sheets. Both sheets fan into the *same* new
# table, same as the old table did, with voice_table_section as a literal
# per sheet (mirrors telus_v2's TLS book: several sheets, one table).
#
# NOT fully masked like the other RCCI books: "Voice Services" row
# AV_P_A / "Advantage Voice Analog" has a real price ($0.95 per Account) —
# every other row is $0.00 / "No Charge" / blank. "Long Distance Rates" is
# fully masked ($0.00 CPM Rate throughout).
_VOICE_COLUMNS = (
    "voice_table_section",
    "service_id",
    "service_name",
    "service_subcategory",
    "service_component",
    "monthly_fixed_fee",
    "cpm_rate",
    "terminating_country",
    "ecf_rate",
    "ecf_unit_of_measure",
)

VOICE_SERVICES_V2 = BookSpec(
    book_code="voice_v2",
    file_match="voice services",
    sheets=(
        SimpleSheetSpec(
            sheet_name="Voice Services",
            table_name="raw_rogers_v2_voice_pricebook",
            columns=_VOICE_COLUMNS,
            feed_code="voice_base_service",
            literal_columns={"voice_table_section": "base_service"},
        ),
        SimpleSheetSpec(
            sheet_name="Long Distance Rates",
            table_name="raw_rogers_v2_voice_pricebook",
            columns=_VOICE_COLUMNS,
            feed_code="voice_long_distance",
            literal_columns={"voice_table_section": "long_distance"},
        ),
    ),
)

# Mirrors the old raw_rogers_professional_services_pricebook exactly (same
# 7 fields) — the old table was built from professional_services.pdf, this
# is the same catalogue as an Excel workbook instead. Unlike the other RCCI
# v2 books, pricing here is NOT masked (real rates throughout).
#
# The workbook also has three other tabs ("TO Change Log", "S&U Price
# Book", "S&U Gap Analysis") that are a QC comparison report against the
# existing raw_data.raw_rogers_professional_services_pricebook table, not
# pricebook data — only the "Professional Services" sheet is ingested here.
PROFESSIONAL_SERVICES_V2 = BookSpec(
    book_code="professional_services_v2",
    file_match="professional services",
    sheets=(
        SimpleSheetSpec(
            sheet_name="Professional Services",
            table_name="raw_rogers_v2_professional_services_pricebook",
            columns=(
                "title",
                "services_supported",
                "service_id",
                "business_hours_rate_hourly",
                "after_business_hours_rate_hourly",
                "minimum_billing_increment",
                "fixed_fee",
            ),
            feed_code="professional_services",
        ),
    ),
)

BOOKS: tuple[BookSpec, ...] = (
    CELLULAR_SERVICES_V2,
    CELLULAR_DEVICES_V2,
    DATA_SERVICES_V2,
    VOICE_SERVICES_V2,
    PROFESSIONAL_SERVICES_V2,
)


def resolve_book(file_stem: str) -> BookSpec:
    stem = file_stem.casefold()
    for book in BOOKS:
        if book.file_match in stem:
            return book
    known = ", ".join(b.file_match for b in BOOKS)
    raise ValueError(f"Unknown Rogers v2 pricebook {file_stem!r}; expected filename containing one of: {known}")


def resolve_sheet(book: BookSpec, sheet_name: str) -> SheetSpec | None:
    target = sheet_name.strip().casefold()
    for spec in book.sheets:
        if spec.sheet_name.strip().casefold() == target:
            return spec
    return None
