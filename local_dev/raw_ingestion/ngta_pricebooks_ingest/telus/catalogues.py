"""Telus NGTA pricebook Excel catalogue definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogueSpec:
    """Maps u_ngta_*.xlsx filenames to a raw Postgres table and column list."""

    file_stem: str
    table_name: str
    columns: tuple[str, ...]
    feed_code: str


def stem_to_table_name(file_stem: str) -> str:
    """u_ngta_cellular_additional_fees_catalogue -> raw_telus_cellular_additional_fees_pricebook."""
    body = file_stem
    if body.casefold().startswith("u_ngta_"):
        body = body[7:]
    if body.casefold().endswith("_catalogue"):
        body = body[: -len("_catalogue")]
    return f"raw_telus_{body}_pricebook"


# file_stem, data columns (ingestion adds pricebook_ingestion_run_id, sheet_name, extras)
_CATALOGUE_ROWS: list[tuple[str, tuple[str, ...]]] = [
    (
        "u_ngta_cellular_additional_fees_catalogue",
        ("service", "fee", "cpm_rate", "type_of_service"),
    ),
    (
        "u_ngta_cellular_catalog_and_price_list",
        ("category", "fee_based_optional_features", "service_id", "monthly_fee"),
    ),
    (
        "u_ngta_cellular_device_catalogue",
        ("device_name", "device_price", "type_of_service"),
    ),
    (
        "u_ngta_cellular_long_distance_cost_per_minute_catalogue",
        ("calling_to", "cpm_rate", "type_of_service"),
    ),
    (
        "u_ngta_cellular_mms_catalogue",
        ("service", "service_id", "monthly_fee", "type_of_service"),
    ),
    (
        "u_ngta_cellular_roaming_catalogue",
        ("roaming", "fee", "type_of_service"),
    ),
    (
        "u_ngta_cellular_services_catalogue",
        ("category", "rate_plan", "service_id", "monthly_fee", "type_of_service"),
    ),
    (
        "u_ngta_control_center_services_catalogue",
        ("category", "rate_plan", "service_id", "monthly_fee"),
    ),
    (
        "u_ngta_data_professional_services_catalogue",
        (
            "professional_service_category",
            "title",
            "service_supported",
            "service_id",
            "business_hours_rate_hourly",
            "after_business_hours_rate_hourly",
        ),
    ),
    (
        "u_ngta_data_services_catalogue",
        (
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
    ),
    (
        "u_ngta_voice_long_distance_fees_catalogue",
        (
            "country",
            "landline_termination_cpm_rate",
            "mobile_termination_cpm_rate",
        ),
    ),
    (
        "u_ngta_voice_professional_services_catalogue",
        (
            "professional_service_category",
            "title",
            "service_supported",
            "service_id",
            "business_hours_rate_hourly",
            "after_business_hours_rate_hourly",
        ),
    ),
    (
        "u_ngta_voice_services_catalogue",
        (
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
    ),
]

CATALOGUES: tuple[CatalogueSpec, ...] = tuple(
    CatalogueSpec(
        file_stem=stem,
        table_name=stem_to_table_name(stem),
        columns=cols,
        feed_code=stem.removeprefix("u_ngta_").removesuffix("_catalogue")
        if stem.endswith("_catalogue")
        else stem.removeprefix("u_ngta_"),
    )
    for stem, cols in _CATALOGUE_ROWS
)

_CATALOGUE_BY_STEM: dict[str, CatalogueSpec] = {
    spec.file_stem.casefold(): spec for spec in CATALOGUES
}


def resolve_catalogue(path_stem: str) -> CatalogueSpec:
    spec = _CATALOGUE_BY_STEM.get(path_stem.casefold())
    if spec is None:
        known = ", ".join(s.file_stem for s in CATALOGUES)
        raise ValueError(f"Unknown Telus catalogue {path_stem!r}; expected one of: {known}")
    return spec
