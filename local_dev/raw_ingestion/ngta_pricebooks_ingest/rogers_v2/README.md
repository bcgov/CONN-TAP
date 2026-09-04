# Rogers (RCCI) NGTA Pricebook v2 — Raw Table Mapping

Five new price books arrived as Excel workbooks, RCCI = Rogers
Communications Canada Inc. (the sender's own name for itself — printed as a
"CONFIDENTIAL Rogers Communications Canada Inc." banner on the Devices
Catalogue's title row).

**Pricing in Cellular Services, Cellular Devices Catalogue, and Data
Services is masked to zero.** Every `Monthly Fixed Fee` / `Price` cell reads
`0`, formatted with a currency number format (`\$0.00` / `\$ #,##0.00`) — so
it renders as text `"$0.00"` on ingestion, not a blank — same situation as
several of the Telus v2 books (see `telus_v2/README.md`, Professional
Services section). Not a real business change, just sanitized source data.
(`ECF Rate` is a genuine, non-masked percentage in Cellular Services, Data
Services, and Voice Services — not a price.)

**Voice Services is a partial exception — it is NOT fully masked.** Its
"Voice Services" sheet has one real, non-zero price: `AV_P_A` / "Advantage
Voice Analog" reads `$0.95 per Account`, while every other row in both
sheets ("Voice Services" and "Long Distance Rates") is `$0.00` / `"No
Charge"` / blank. Verified by scanning every row's `Monthly Fixed
Fee`/`CPM Rate` value, not just a sample. `AV_P_A` isn't a new item either —
it exists in the old book too — so this is a masking miss on an existing
service, not a newly-introduced one. Worth confirming with Rogers whether
that's a real price that slipped through their masking pass or intentional.

**Professional Services is not masked at all.** Real, non-zero rates
throughout (hourly rates, fixed fees, per-device rates). The workbook also
ships three QC tabs (`TO Change Log`, `S&U Price Book`, `S&U Gap Analysis`)
comparing the "Professional Services" tab against the existing
`raw_data.raw_rogers_professional_services_pricebook` table — those are a
validation report, not pricebook data, and are not ingested; see
`catalogues.py` for the reasoning. Only the "Professional Services" sheet
feeds `raw_rogers_v2_professional_services_pricebook`.

## Old tables (`raw_data`) → New tables (`raw_data_v2`)

| Old table | Old fields | New table | New fields |
|---|---|---|---|
| `raw_rogers_cellular_pricebook` (PDF: `cellular.pdf`) | service_id, service_name, service_component, speed_mbps_or_capacity_mb, monthly_fixed_fee, ecf_rate, rlh_roam_like_home_usa_overage_fee, rlh_roam_like_home_intl_overage_fee, ecf_unit_of_measure, fixed_fee, overage_charge | `raw_rogers_v2_cellular_pricebook` | *(identical — same 11 columns)* |
| `raw_rogers_data_pricebook` (PDF: `data.pdf`) | service_id, service_name, service_component, speed_mbps_or_capacity_mb, monthly_fixed_fee, ecf_rate, ecf_unit_of_measure | `raw_rogers_v2_data_pricebook` | *(identical — same 7 columns)* |
| `raw_rogers_voice_pricebook` (PDF: `voice.pdf`, 2 tables: base_service, long_distance) | voice_table_section, service_id, service_name, service_subcategory, service_component, monthly_fixed_fee, cpm_rate, terminating_country, ecf_rate, ecf_unit_of_measure | `raw_rogers_v2_voice_pricebook` | *(identical — same 10 columns)* |
| `raw_rogers_professional_services_pricebook` (PDF: `professional_services.pdf`) | title, services_supported, service_id, business_hours_rate_hourly, after_business_hours_rate_hourly, minimum_billing_increment, fixed_fee | `raw_rogers_v2_professional_services_pricebook` | *(identical — same 7 columns)* |

All four new workbooks use the exact same column headers as their old PDF
tables — same catalogues, Excel instead of PDF, no schema drift. The Voice
Services book's two sheets ("Voice Services" = old table's `base_service`
section, "Long Distance Rates" = old table's `long_distance` section) fan
into the one new table exactly as the old table already combined them, with
`voice_table_section` as a literal per sheet (same technique telus_v2 used
for its 8-sheet Time Limited Services book).

Percentage-formatted `ECF Rate` cells (`0%`, e.g. `0.25` -> `"25%"`, seen in
Data Services and Voice Services) and plain-text `ECF Rate` cells (`"n/a"`,
seen in Cellular Services) are both handled by `rogers_v2/excel.py`'s
`as_text`, same currency-or-percentage number-format handling telus_v2 uses.

## Item-level diff (old book vs new file, by service ID)

Old-side data came from a person pasting rows out of the actual old
PDF-derived catalogue (not a database export), so this is a real diff, same
rigor as the Telus v2 books' diffs — every ID compared, not sampled.

| Book | Old count | New count | Missing (in old, not new) | Added (in new, not old) |
|---|---|---|---|---|
| Cellular Services | 109 | 122 | none | **13**: a new "Stadium" capacity tier in IoT Rogers Control Centre — `CCAS500GB` through `CCAS100TB` (500GB→100TB, 11 sizes) plus `CCAAP` ("Ctrl Ctr Stadium &PFF + Satellite") and `CCASTM_PPU` ("Satellite to IoT PPU") |
| Data Services | 303 | 345 | none | **42**: all in Ethernet Virtual Private Line — extends the existing Virtual Path speed ladder upward (600/700/800/900Mbps, 1/2/3/4/5/10Gbps, each BE/Priority/Real_Time/Standard) and adds 1G/10G/100G Access tiers (each with a plain and a "Preferred Location" variant) |
| Voice Services — base_service | 55 | 55 | none | none |
| Voice Services — long_distance | 76 rows (country names not captured in the pasted diff) | 76 | not verified — see note | not verified — see note |
| Professional Services | 35 | 35 | none | none |

Notes:
- **Professional Services**: exact same 35 service IDs both sides, no
  additions or removals — only the "Professional Services" sheet was
  compared (title/services_supported/service_id), not the S&U tabs. Rate
  values weren't part of the pasted old-side data, so this confirms the
  item set is unchanged, not whether any individual rate moved.
- **No removals anywhere.** Every old service ID in Cellular Services, Data
  Services, and Voice Services base_service survives unchanged into the new
  file, same name/component text.
- **Voice Services long_distance**: only a row count was available for the
  old side (the pasted comparison didn't include the `Terminating Country`
  column), so the 76-vs-76 match confirms count parity only, not that it's
  the same 76 countries. `scripts/sql/rogers_v2_pricebook_diff.sql` will
  confirm this exactly (keyed on `service_id` + `terminating_country`) once
  `raw_data.raw_rogers_voice_pricebook` has real old data loaded.
- **Cellular Devices Catalogue**: no old table exists to diff against at
  all — see below.

## New table with no old table

| New table | New fields |
|---|---|
| `raw_rogers_v2_cellular_device_pricebook` | status, service_id, device_name, type, brand, model, series, trim, capacity, color, price |

Rogers pricebook ingestion never had a device catalogue feed before this —
`rogers/parsers/` only ever covered cellular/data/voice/professional_services
(all PDF). Source: `RCCI NGTA Cellular Devices Catalogue v1.0.xlsx`, sheet
"Cellular Devices Catalogue", header on row 2 (row 1 is the confidentiality
banner, merged A1:K1).
