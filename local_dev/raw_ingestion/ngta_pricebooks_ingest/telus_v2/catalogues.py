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


@dataclass(frozen=True)
class SplitByValueSheetSpec:
    """One sheet whose rows fan out into several tables based on a column's
    value, e.g. "Data & Voice Fees" has a Service Category column of
    'Data'/'Voice' and each old table (raw_telus_data_services_pricebook,
    raw_telus_voice_services_pricebook) already existed as its own file —
    this preserves that old table boundary instead of merging them."""

    sheet_name: str
    split_column: str  # canonical column name whose value selects the table
    table_by_value: dict[str, str]  # {"data": table_name, "voice": table_name} — keys casefolded
    columns: tuple[str, ...]
    feed_code: str
    header_row: int = 1


SheetSpec = SimpleSheetSpec | MultiBlockSheetSpec | SplitByValueSheetSpec


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

VOICE_AND_DATA_V2 = BookSpec(
    book_code="voice_and_data_v2",
    file_match="voice and data",
    sheets=(
        # Mirrors the old raw_telus_data_services_pricebook /
        # raw_telus_voice_services_pricebook split: those were two separate
        # old files (identical column shape, each internally one constant
        # Service Category), now merged into one sheet in the new workbook.
        # Splitting by the sheet's own Service Category column preserves the
        # old table boundary instead of introducing a new merged table.
        SplitByValueSheetSpec(
            sheet_name="Data & Voice Fees",
            split_column="service_category",
            table_by_value={
                "data": "raw_telus_v2_data_services_pricebook",
                "voice": "raw_telus_v2_voice_services_pricebook",
            },
            columns=(
                "service_category",
                "service_id",
                "service_name",
                "short_service_description",
                "monthly_fee",
                "ecf_rate",
                "service_sla",
                "technical_services_support",
                "ordering_lead_times_objectives",
                "delivery_lead_times_objectives_service_interval",
                "technical_service_standards",
            ),
            feed_code="data_voice_services",
            header_row=5,
        ),
        # Mirrors the old raw_telus_voice_long_distance_fees_pricebook exactly.
        SimpleSheetSpec(
            sheet_name="LD International Fees",
            table_name="raw_telus_v2_voice_long_distance_fees_pricebook",
            columns=("country", "landline_termination_cpm_rate", "mobile_termination_cpm_rate"),
            feed_code="voice_long_distance_fees",
            header_row=4,
        ),
        # New catalogue, no old precedent: usage/CPM rates for toll-free,
        # SIP trunking, long distance, and ice Contact Centre features that
        # used to live as flat rows inside the old voice_services catalogue
        # (moved out here since they're usage-based, not flat monthly fees).
        MultiBlockSheetSpec(
            sheet_name="CPM-Usage Rates",
            table_name="raw_telus_v2_voice_data_usage_rates_pricebook",
            columns=("id_type", "service_id", "service", "description", "rate_type", "rate"),
            feed_code="voice_data_usage_rates",
            parser="voice_data_usage_rates",
        ),
    ),
)

_TLS_COLUMNS = (
    "product",
    "service_category",
    "service_name",
    "service_id",
    "id_type",
    "short_service_description",
    "monthly_fee",
    "overage_charges",
)

TIME_LIMITED_SERVICES_V2 = BookSpec(
    book_code="time_limited_services_v2",
    file_match="time limited services",
    sheets=(
        # No old raw_telus_* table exists for any of these 8 sheets — the
        # old schema never had a "Time Limited Services" pricebook file, so
        # there's nothing to mirror here. All 8 share one table
        # (raw_telus_v2_tls_pricebook), with `product` naming which sheet a
        # row came from and unused columns left NULL per sheet (e.g.
        # `overage_charges` is SIPA-V1-only). "Service ID/ Billing ID" and
        # SIPA's "Service ID" both canonicalize to `service_id` (see
        # HEADER_OVERRIDES in excel.py) since they're the same concept
        # under different header wording, never both present on one sheet.
        #
        # SIPA V1 has a second, real service ID (Monthly Top Up) on 5 of its
        # 15 rows — an alternate billing code for the same add-on, not a
        # separately-priced item. Unpivoted so both IDs are independently
        # queryable rows (needed for spend/validation lookups by
        # service_id): id_type distinguishes 'base' from 'monthly_top_up'.
        # The top-up row's monthly_fee is left NULL (this sheet has no
        # distinct price for it) while overage_charges carries over
        # unchanged, since that rate applies to the add-on either way.
        MultiBlockSheetSpec(
            sheet_name="SIPA V1",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_sipa_v1",
            parser="tls_sipa_v1",
        ),
        SimpleSheetSpec(
            sheet_name="Analog Private Line",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_analog_private_line",
            header_row=2,
            literal_columns={"product": "Analog Private Line"},
        ),
        SimpleSheetSpec(
            sheet_name="Centrex",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_centrex",
            header_row=2,
            literal_columns={"product": "Centrex"},
        ),
        SimpleSheetSpec(
            sheet_name="Carrier Optical Ethernet",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_carrier_optical_ethernet",
            header_row=2,
            literal_columns={"product": "Carrier Optical Ethernet"},
        ),
        SimpleSheetSpec(
            sheet_name="Managed Router",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_managed_router",
            header_row=2,
            literal_columns={"product": "Managed Router"},
        ),
        SimpleSheetSpec(
            sheet_name="Copper Services",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_copper_services",
            header_row=2,
            literal_columns={"product": "Copper Services"},
        ),
        SimpleSheetSpec(
            sheet_name="ADSL Services",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_adsl_services",
            header_row=2,
            literal_columns={"product": "ADSL Services"},
        ),
        SimpleSheetSpec(
            sheet_name="IP Trunking R2",
            table_name="raw_telus_v2_tls_pricebook",
            columns=_TLS_COLUMNS,
            feed_code="tls_ip_trunking_r2",
            header_row=2,
            literal_columns={"product": "IP Trunking R2"},
        ),
    ),
)

PROFESSIONAL_SERVICES_V2 = BookSpec(
    book_code="professional_services_v2",
    file_match="professional services",
    sheets=(
        # Old raw_telus_data_professional_services_pricebook and
        # raw_telus_voice_professional_services_pricebook had IDENTICAL
        # (title, service_id) key sets (verified against the real old
        # files) — they were duplicate copies of the same catalogue, not a
        # genuine data/voice split. The new workbook consolidates them into
        # one sheet, so this merges into one new table too, matching what
        # the new file actually is rather than preserving a redundant old
        # split. 70 of 71 rows match the old catalogues exactly; 1 new item
        # ("Intelliroute Professional Service").
        MultiBlockSheetSpec(
            sheet_name="Professional Services",
            table_name="raw_telus_v2_professional_services_pricebook",
            columns=(
                "professional_service_category",
                "title",
                "service_supported",
                "service_id",
                "business_hours_rate_hourly",
                "after_business_hours_rate_hourly",
            ),
            feed_code="professional_services",
            parser="professional_services",
        ),
        # New catalogue, no old precedent: one-time setup/activation fees
        # supporting the Connected Worker family from the Cellular Services
        # v2.0 book (Connected Worker Solution / Hardware / Usage Rate).
        SimpleSheetSpec(
            sheet_name="Connected Worker Pro Svcs",
            table_name="raw_telus_v2_connected_worker_professional_services_pricebook",
            columns=("item", "description", "service_id", "rate", "dependencies"),
            feed_code="connected_worker_professional_services",
            header_row=6,
        ),
    ),
)

BOOKS: tuple[BookSpec, ...] = (
    CELLULAR_SERVICES_V2,
    CELLULAR_DEVICES_V2,
    VOICE_AND_DATA_V2,
    TIME_LIMITED_SERVICES_V2,
    PROFESSIONAL_SERVICES_V2,
)


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
