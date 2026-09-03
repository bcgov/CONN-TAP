# Telus NGTA Pricebook v2 — Raw Table Mapping

DDL: [`alembic/raw_data/ngta_pricebooks_v2.sql`](../../../../app/backend/alembic/raw_data/ngta_pricebooks_v2.sql)
Migration: [`007_telus_ngta_pricebook_v2.py`](../../../../app/backend/alembic/versions/007_telus_ngta_pricebook_v2.py)

**Bold** = column added in the new table. ~~Strikethrough~~ = old column not
carried over (dropped, or renamed — renames are shown as `old → new`).
`type_of_service` was a constant literal in each old file — it's hardcoded
back into every new table that had it, since the new sheets don't repeat
that column themselves.

## Old tables (`raw_data`) → New tables (`raw_data_v2`)

| Old table | Old fields | New table | New fields |
|---|---|---|---|
| `raw_telus_cellular_services_pricebook` | category, rate_plan, service_id, monthly_fee, type_of_service | `raw_telus_v2_cellular_services_pricebook` | category, rate_plan, service_id, monthly_fee, type_of_service *(identical)* |
| `raw_telus_cellular_additional_fees_pricebook` | service, fee, cpm_rate, type_of_service | `raw_telus_v2_cellular_additional_fee_based_features_pricebook` | service, **service_id**, fee, cpm_rate, type_of_service |
| `raw_telus_cellular_roaming_pricebook` | roaming, fee, type_of_service | `raw_telus_v2_cellular_roaming_pricebook` | roaming, fee, type_of_service *(identical)* |
| `raw_telus_cellular_long_distance_cost_per_minute_pricebook` | calling_to, cpm_rate, type_of_service | `raw_telus_v2_cellular_long_distance_pricebook` | calling_to, cpm_rate, type_of_service *(identical)* |
| `raw_telus_cellular_mms_pricebook` | service, service_id, monthly_fee, type_of_service | `raw_telus_v2_cellular_mms_pricebook` | service, service_id, monthly_fee, **incident_cap**, type_of_service |
| `raw_telus_cellular_catalog_and_price_list_pricebook` | category, ~~fee_based_optional_features → item_description~~, service_id, monthly_fee | `raw_telus_v2_control_center_pricebook` | **section**, category, item_description, service_id, monthly_fee, **overage_charges**, **fee_type** |
| `raw_telus_control_center_services_pricebook` | category, ~~rate_plan → item_description~~, service_id, monthly_fee | `raw_telus_v2_control_center_pricebook` | **section**, category, item_description, service_id, monthly_fee, **overage_charges**, **fee_type** |
| `raw_telus_cellular_device_pricebook` | device_name, device_price, type_of_service | `raw_telus_v2_cellular_device_pricebook` | device_name, device_price, type_of_service *(identical)* |

## New tables with no old table

| New table | New fields |
|---|---|
| `raw_telus_v2_gms_pricebook` | service, service_id, monthly_fee |
| `raw_telus_v2_gms_usage_rate_pricebook` | service, usage_rate, detail |
| `raw_telus_v2_fleet_complete_pricebook` | section, item, description, code, price |
| `raw_telus_v2_connected_worker_pricebook` | section, item, description, service_id, monthly_fee, dependencies |
| `raw_telus_v2_connected_worker_usage_rate_pricebook` | item, description, service_id, usage_rate |
| `raw_telus_v2_connected_worker_hardware_pricebook` | item, description, service_id, price, dependencies |

## Item-level diff (old file vs new file, by service ID / name)

Row-count matches don't guarantee the same items — this is a per-section
diff of actual service IDs / names, old source files vs the new workbook.

| Section | Old count | New count | Missing (in old, not new) | Added (in new, not old) |
|---|---|---|---|---|
| Cellular Services | 21 | 21 | none | none |
| Basic Fee-Based Features | 9 | 9 | none | none |
| Advanced Fee-Based features | 2 | 14 | none | **12**: Organizational Hierarchy, Approval Workflow, End-User Ordering, Historical Reporting, Custom Catalogue, Asset Management, Smart Alerts, Reporting Scheduler, Subscriber 360, API Integration, IQ Premium Bundle (Full), IQ Premium Bundle (Bundle A) — new "IQ Premium" product line |
| Additional Fee-Based Features | 4 | 6 | none | **2**: Call Forwarding Long Distance, Outgoing Call Deny (first row in this catalogue to carry a real service ID, `SCDORF`) |
| Roaming | 2 | 2 | none | none |
| Long Distance | 241 | 241 | none | none — but see data-quality note below |
| MMS | 7 | 7 | none (see note below) | none |
| Control Center *(old catalog_and_price_list + control_center_services combined)* | 13 | 25 | **1**: `NGTA Access + private APN` (old service ID `2311214`) | **13**: Pooled Rate Plans tier (10 items, `NGTA 2000`–`2009`, 50MB–250GB) + SIM pricing block (3 items: Standard/Industrial physical SIM, eSIM QR Voucher) |
| Cellular Devices Catalogue | 86 | 86 | none | none — but see data-quality note below |

Notes:
- **Cellular Devices Catalogue — prices**: the old file had real prices for
  73/86 devices; the new file has device_price blank on **all 86** rows
  (more thoroughly masked than the Cellular Services file's `$x.xx`
  placeholders).
- **MMS bundle rows** ("BYOD (3)", "Corp Bundle (5)"): the old file's
  free-text service-ID list was truncated mid-string; the new file has the
  full untruncated text. Same 7 services on both sides — not a real content
  change, just a data-quality artifact in the old file.
- **Long Distance — Guinea-Bissau**: the new file's country name contains an
  embedded control character (`_x001E_`), e.g. `Guinea‑<0x1E>Bissau` instead
  of a clean hyphen. Invisible in Excel but will break exact-string
  joins/lookups downstream if not cleaned before load.
- **Control Center — `NGTA Access + private APN`**: no counterpart found in
  the new file (fuzzy name-matched against all 25 new items) — worth
  confirming with Telus whether it was dropped or folded into another item.

---

# Voice and Data book

Source: `TCI NGTA Price Book Voice and Data v2.9.xlsx`, 3 sheets (`Data &
Voice Fees`, `CPM-Usage Rates`, `LD International Fees`), diffed against the
real old files `u_ngta_data_services_catalogue.xlsx`,
`u_ngta_voice_services_catalogue.xlsx`,
`u_ngta_voice_long_distance_fees_catalogue.xlsx`.

**New pattern**: `Data & Voice Fees` is one sheet with a `Service Category`
column (`Data`/`Voice`) instead of two separate old-style files. Rather than
merge it into one new table, ingestion splits it back into two tables by
that column's value — preserving the old table boundary (`data_services` /
`voice_services` were always separate old files with identical column
shape), the same principle as the `type_of_service` merge above, just
applied in the opposite direction.

Also confirmed here: real prices in this workbook are numeric cells with
Excel currency (`"$"#,##0.00`) and percentage (`0%`) formatting, not literal
"$"/"%" text like the old catalogues — ingestion renders `monthly_fee` as
`"$345.00"` and `ecf_rate` as `"25%"` to match the old text convention
either way.

## Old tables (`raw_data`) → New tables (`raw_data_v2`)

| Old table | Old fields | New table | New fields |
|---|---|---|---|
| `raw_telus_data_services_pricebook` | service_category, service_id, service_name, short_service_description, monthly_fee, ecf_rate, service_sla, technical_services_support, ordering_lead_times_objectives, delivery_lead_times_objectives_service_interval, technical_service_standards | `raw_telus_v2_data_services_pricebook` | *(identical — same 11 columns)* |
| `raw_telus_voice_services_pricebook` | *(same 11 columns as above)* | `raw_telus_v2_voice_services_pricebook` | *(identical — same 11 columns)* |
| `raw_telus_voice_long_distance_fees_pricebook` | country, landline_termination_cpm_rate, mobile_termination_cpm_rate | `raw_telus_v2_voice_long_distance_fees_pricebook` | *(identical)* |

## New tables with no old table

| New table | New fields |
|---|---|
| `raw_telus_v2_voice_data_usage_rates_pricebook` | id_type, service_id, service, description, rate_type, rate |

`CPM-Usage Rates` packs 6 repeating header blocks onto one sheet (header
labels vary: `Service ID` vs `Parent Service ID`, `Usage Rate` vs `CPM
Rate`) — `id_type`/`rate_type` record which variant each row's block used,
same technique as Control Center's `section` column.

## Item-level diff (old file vs new file, by service ID / name)

| Section | Old count | New count | Missing (in old, not new) | Added (in new, not old) |
|---|---|---|---|---|
| Data Services | 186 | 186 | none | none |
| Voice Services | 285 | 310 | **10** — see note below | **22**: new Cloud Fax Service (`NG024`–`NG035`, ~8 items), 7 more "ice Contact Centre" fee-based features, `NGLL27` (Business Line optional feature), `TEL1010` (Cloud PBX optional feature), 1 SIP Trunking item |
| LD International Fees | 231 | 231 | none | none |
| CPM-Usage Rates | 0 (new) | 22 | — | all new |

Notes:
- **Voice Services — the 10 "missing" items aren't gone, they moved**: every
  one of them (Toll Free `COURTESY RESPONSE`/`CALL PROMPTER`/`DATABASE
  ROUTING`/`ENROUTE`, `NGTFDOM`, `NGLDDOM`, and 4 "ice Contact Centre"
  usage-based features) now appears as a row in the new `CPM-Usage Rates`
  sheet instead — a genuine reclassification (usage-based rate, not a flat
  monthly fee), not a dropped service. Confirmed by matching service ID
  across both sheets.
- **ECF Rate / ordering & delivery lead-time columns**: several old-style
  column names needed fuzzy header matching (not exact match) because the
  new sheet's header text carries extra subtitle text, e.g. `"Service
  SLA\nService Levels are described in Service Descriptions"` instead of
  just `"Service SLA"`, and singular `"Ordering Lead Time Objectives"`
  instead of the old plural `"Ordering Lead Times Objectives"`. Handled the
  same way the old `telus/excel.py` handled similar header drift.
