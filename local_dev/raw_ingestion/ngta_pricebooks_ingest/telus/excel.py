"""Parse Telus pricebook Excel workbooks into row dicts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from telus.catalogues import CatalogueSpec

HEADER_OVERRIDES: dict[str, str] = {
    "service_id": "service_id",
    "serviceid": "service_id",
    "fee_based_optional_features": "fee_based_optional_features",
    "type_of_service": "type_of_service",
    "professional_service_category": "professional_service_category",
    "service_supported": "service_supported",
    "services_supported": "service_supported",
    "business_hours_rate_hourly": "business_hours_rate_hourly",
    "after_business_hours_rate_hourly": "after_business_hours_rate_hourly",
    "short_service_description": "short_service_description",
    "ecf_rate": "ecf_rate",
    "service_sla": "service_sla",
    "technical_services_support": "technical_services_support",
    "technical_service_support": "technical_services_support",
    "ordering_lead_times_objectives": "ordering_lead_times_objectives",
    "delivery_lead_times_objectives_service_interval": (
        "delivery_lead_times_objectives_service_interval"
    ),
    "technical_service_standards": "technical_service_standards",
    "landline_termination_cpm_rate": "landline_termination_cpm_rate",
    "mobile_termination_cpm_rate": "mobile_termination_cpm_rate",
    "calling_to": "calling_to",
    "cpm_rate": "cpm_rate",
    "rate_plan": "rate_plan",
    "monthly_fee": "monthly_fee",
    "device_name": "device_name",
    "device_price": "device_price",
}


def canonical_header(name: Any) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    s = str(name).replace("\u00a0", " ").strip()
    if not s or s.lower().startswith("unnamed"):
        return ""
    s = re.sub(r"\s+", " ", s.lower())
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if s in HEADER_OVERRIDES:
        return HEADER_OVERRIDES[s]
    if "landline" in s and "termination" in s and "cpm" in s:
        return "landline_termination_cpm_rate"
    if "mobile" in s and "termination" in s and "cpm" in s:
        return "mobile_termination_cpm_rate"
    if "business_hours" in s and "hourly" in s:
        return "business_hours_rate_hourly"
    if "after" in s and "business" in s and "hourly" in s:
        return "after_business_hours_rate_hourly"
    if "delivery" in s and "lead" in s and "interval" in s:
        return "delivery_lead_times_objectives_service_interval"
    if "fee_based" in s and "optional" in s:
        return "fee_based_optional_features"
    return s


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")
    if not df.empty:
        mask_header = df.apply(lambda row: list(row.values) == list(df.columns), axis=1)
        df = df[~mask_header]
    return df.loc[:, ~df.columns.duplicated()]


def as_text(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def parse_workbook(path: Path, spec: CatalogueSpec) -> list[dict[str, Any]]:
    xl = pd.ExcelFile(path)
    rows_out: list[dict[str, Any]] = []
    db_cols = frozenset(spec.columns)

    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name, dtype=object)
        df = clean_frame(df)
        if df.empty:
            continue

        colmap = {c: canonical_header(c) for c in df.columns}
        for _, row in df.iterrows():
            vals: dict[str, Any] = {
                "pricebook_ingestion_run_id": None,
                "sheet_name": sheet_name,
                "extras": None,
            }
            extras: dict[str, Any] = {}
            for excel_col, db in colmap.items():
                if not db:
                    continue
                val = row.get(excel_col)
                text = as_text(val)
                if db in db_cols:
                    vals[db] = text
                elif text is not None:
                    extras[str(excel_col)] = text

            if not any(vals.get(c) for c in spec.columns):
                continue
            if extras:
                vals["extras"] = json.dumps(extras)
            rows_out.append(vals)

    return rows_out
