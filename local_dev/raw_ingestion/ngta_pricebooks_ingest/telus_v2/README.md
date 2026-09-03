# Telus NGTA Pricebook v2 — Raw Table Mapping

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
| Cellular Devices Catalogue | 86 | 86 | none | none |

Notes:
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
| Voice Services | 285 | 310 | **10** moved — see note below | **22**: new Cloud Fax Service (`NG024`–`NG035`, ~8 items), 7 more "ice Contact Centre" fee-based features, `NGLL27` (Business Line optional feature), `TEL1010` (Cloud PBX optional feature), 1 SIP Trunking item |
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

---

# Time Limited Services book

Source: `TCI NGTA Price Book Time Limited Services (Combined) v1.7.xlsx`, 8
sheets, each a distinct legacy product (SIPA V1, Analog Private Line,
Centrex, Carrier Optical Ethernet, Managed Router, Copper Services, ADSL
Services, IP Trunking R2).

**No old→new mapping exists for this book.** Unlike Cellular Services and
Voice and Data, there's no old `raw_telus_*` table for any of these 8
products — the old schema never had a "Time Limited Services" pricebook
file, and no old source file for it has been added to the repo. This is
confirmed, not assumed: I checked `scripts/old price books/` and the
original `ngta_pricebooks.sql` DDL, and neither has anything matching these
product names. If an old file surfaces later, this section should be
redone as an old→new diff like the others above.

Each sheet has its own single header row (no repeating blocks). Column
shapes differ per sheet (some have a service ID, some don't; only SIPA V1
has overage charges), but there's no old-schema precedent either way, so —
per your call — all 8 share **one table**, `raw_telus_v2_tls_pricebook`,
with a `product` column naming which sheet a row came from and columns a
given sheet doesn't use left `NULL`.

## One combined table (no old table to compare against)

| New table | Columns |
|---|---|
| `raw_telus_v2_tls_pricebook` | product, service_category, service_name, service_id, id_type, short_service_description, monthly_fee, overage_charges |

| `product` value | Source sheet | Columns populated (beyond product/service_category/service_name/monthly_fee) | Row count |
|---|---|---|---|
| `SIPA V1` | SIPA V1 | service_id, id_type, overage_charges | 20 (see below) |
| `Analog Private Line` | Analog Private Line | short_service_description | 43 |
| `Centrex` | Centrex | short_service_description | 58 |
| `Carrier Optical Ethernet` | Carrier Optical Ethernet | service_id | 7 |
| `Managed Router` | Managed Router | short_service_description | 3 |
| `Copper Services` | Copper Services | service_id | 40 |
| `ADSL Services` | ADSL Services | short_service_description | 40 |
| `IP Trunking R2` | IP Trunking R2 | service_id | 10 |

`Service ID/ Billing ID` (Carrier Optical Ethernet, Copper Services, IP
Trunking R2) and SIPA V1's `Service ID` both land in the same `service_id`
column — same concept, just worded differently per sheet, and never both
present on one sheet — so there's no ambiguity in reusing one column for it.

Row counts (verified against the actual file): 20 (SIPA V1, see below) + 43 +
58 + 7 + 3 + 40 + 40 + 10 = **221 rows total**.

## SIPA V1 — unpivoted service IDs

Unlike the other 7 sheets, SIPA V1 has a second, real service ID column
("Service ID (Monthly Top Up)") on 5 of its 15 real rows — an alternate
billing code for the same add-on (e.g. `XSTSM10G` base vs `XS10GBTUP`
top-up), not a separately-priced item. Since downstream lookups need to
match a spend row's `service_id` directly, this table is unpivoted: every
row gets an `id_type` of `'base'` or `'monthly_top_up'`, and each real
service ID — base or top-up — is its own row rather than two IDs packed
into one row.

- 15 real rows → 15 `'base'` rows (unchanged shape/values).
- 5 of those rows also produce a `'monthly_top_up'` row: same
  `service_category`/`service_name`/`short_service_description`, `service_id`
  = the top-up ID, `overage_charges` copied across unchanged (it's the same
  underlying add-on's usage rate either way), **`monthly_fee` left `NULL`**
  — the sheet has no distinct price for the top-up variant, so it's left
  honestly unknown rather than guessed or borrowed from `overage_charges`
  (which is a per-MB usage rate, not a monthly fee — a different unit
  entirely).
- Total: 15 + 5 = 20 rows.
- Bonus fix from this change: 3 footnote rows ("* As per specific M2M
  Shared Add-on", etc.) that the generic single-header parser was
  previously picking up as spurious data rows are now correctly excluded.

`id_type` reuses the same naming convention as
`raw_telus_v2_voice_data_usage_rates_pricebook.id_type` in the Voice and
Data book, which already distinguishes `'Service ID'` vs `'Parent Service
ID'` rows the same way.

Notes:
- **Carrier Optical Ethernet — a footnote is silently dropped**: row 3 has a
  billing-correction note ("Note: SS1RN433306 is billed at $9,650 and
  $2,685...") in an unnamed column (no header text above it). Unnamed
  columns are excluded from the column map entirely — including from
  `extras` — so this text is lost on ingestion. This is a pre-existing
  limitation from the very first version of this pipeline (`telus/excel.py`
  had the same behavior for the old catalogues), not something new to this
  book, and low-stakes here since it's a one-off note rather than price
  data — flagging for awareness, not fixed.

---

# Professional Services book

Source: `TCI NGTA Price Book Professional Services v1.1.xlsx`, 2 sheets
(`Professional Services`, `Connected Worker Pro Svcs`), diffed against the
real old files `u_ngta_data_professional_services_catalogue.xlsx` and
`u_ngta_voice_professional_services_catalogue.xlsx`.

**Finding: the two old files were duplicates on structure, not on price.**
Unlike Data/Voice Services (which had a genuine `Service Category` column
partitioning rows into `Data` vs `Voice`), `raw_telus_data_professional_services_pricebook`
and `raw_telus_voice_professional_services_pricebook` have **identical**
`(category, title, service_supported, service_id)` values on all 70 rows —
verified with a full-row multiset comparison, not just a set, so duplicate
rows and counts are checked too. Same 70 professional-service roles, same
service IDs, listed twice under different filenames. The new workbook's
single `Professional Services` sheet consolidates them structurally, so
this merges into one new table too — not because I chose to merge, but
because that's what the new file actually is.

**Rates are a different story.** `old_data` and `old_voice` don't even
match each other on `business_hours_rate_hourly`/`after_business_hours_rate_hourly`
— each was masked with its own independent incrementing placeholder
sequence (`$0.00, $0.01, $0.02...`). The new file was masked a third way
(flat `$0.00` on nearly every row). Of the 70 shared rows, only 2
coincidentally match one of the old files' rate values — the other 68
differ from both. This isn't a real business change, just three
independently-sanitized test copies with unrelated placeholder pricing —
but it means rates are **not** safe to treat as continuous with the old
data the way the service IDs are.

## Old tables (`raw_data`) → New table (`raw_data_v2`)

| Old table | Old fields | New table | New fields |
|---|---|---|---|
| `raw_telus_data_professional_services_pricebook` + `raw_telus_voice_professional_services_pricebook` (duplicate content) | professional_service_category, title, service_supported, service_id, business_hours_rate_hourly, after_business_hours_rate_hourly | `raw_telus_v2_professional_services_pricebook` | *(identical — same 6 columns)* |

## New table with no old table

| New table | Source sheet | Columns |
|---|---|---|
| `raw_telus_v2_connected_worker_professional_services_pricebook` | Connected Worker Pro Svcs | item, description, service_id, rate, dependencies |

New catalogue, no old precedent: one-time setup/activation fees (e.g.
`NGTA-PS-TCW-SETUP-PERUSER`, `NGTA-PS-BIVY-SETUP`, `NGTA-PS-GARMIN-SETUP`,
`NGTA-PS-SATACTIVATION`) supporting the Connected Worker family already
built in the Cellular Services v2.0 book (Connected Worker Solution /
Hardware / Usage Rate).

## Item-level diff

| Section | Old count | New count | Missing (in old, not new) | Added (in new, not old) |
|---|---|---|---|---|
| Professional Services | 70 (both old files, identical) | 71 | none | **1**: "Intelliroute Professional Service" — "Intelliroute Set Up Fee" |
| Connected Worker Pro Svcs | 0 (new) | 7 | — | all new |

Notes:
- **Section-banner rows** (e.g. `"Billing and Reporting"`, `"Project /
  Program Management"`) sit above groups of real rows with only column A
  populated and no `Title` — skipped outright rather than forward-filled,
  since every real row already carries its own (more specific)
  `professional_service_category` value directly (e.g. `"Voice/Data /
  Cellular Billing"`), unlike Cellular Services' merged-cell `Category`
  column which genuinely needed fill-down.
