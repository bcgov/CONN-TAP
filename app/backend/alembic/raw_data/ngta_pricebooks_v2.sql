-- Telus NGTA pricebook v2 raw landing (new multi-sheet workbook format).
-- Apply: cd app/backend && alembic upgrade head
--
-- Source: single multi-sheet workbooks such as
-- "TCI NGTA Price Book Cellular Services v2.0.xlsx" (one sheet per catalogue
-- below), replacing the old one-file-per-catalogue u_ngta_*.xlsx layout.
--
-- Lives in its own raw_data_v2 schema, separate from raw_data, so the new
-- tables never collide with (or get mixed up with) the original raw_telus_*
-- tables in ngta_pricebooks.sql. pricebook_ingestion_run bookkeeping is
-- shared and stays in raw_data (referenced cross-schema below).

CREATE SCHEMA IF NOT EXISTS raw_data_v2;

-- Mirrors the old raw_telus_cellular_services_pricebook: the old
-- u_ngta_cellular_services_catalogue.xlsx was itself a single file covering
-- the Cellular Services / Basic Fee-Based Features / Advanced Fee-Based
-- features groups, distinguished only by type_of_service. The new workbook
-- splits those into three sheets (Cellular Services, Basic Fee-Based
-- Features, Advanced Fee-Based features); this table recombines them the
-- same way the old table did, with type_of_service holding the sheet name
-- each row came from.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  category text, rate_plan text, service_id text, monthly_fee text, type_of_service text,
  extras jsonb
);

-- type_of_service was a constant in each old file below (confirmed against
-- the real old source files) — hardcoded back in here as a literal per
-- sheet, same as raw_telus_v2_cellular_services_pricebook above, since the
-- new sheets don't carry that column themselves.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_additional_fee_based_features_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service text, service_id text, fee text, cpm_rate text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_roaming_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  roaming text, fee text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_long_distance_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  calling_to text, cpm_rate text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_mms_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service text, service_id text, monthly_fee text, incident_cap text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_gms_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service text, service_id text, monthly_fee text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_gms_usage_rate_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service text, usage_rate text, detail text,
  extras jsonb
);

-- Multi-section sheet: Stadium / Pooled rate plans, Fee-Based Optional
-- Features (APN, Static IP), and SIM pricing all live on one sheet with
-- repeating header rows. `section` captures which block a row came from.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_control_center_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  section text, category text, item_description text, service_id text,
  monthly_fee text, overage_charges text, fee_type text,
  extras jsonb
);

-- Multi-section sheet: Monthly Rate Plans, Fee-Based Optional Features,
-- Hardware, and Professional Services blocks with repeating headers.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_fleet_complete_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  section text, item text, description text, code text, price text,
  extras jsonb
);

-- Multi-section sheet: Monthly Rate Plans and Fee-Based Optional Features
-- blocks with repeating headers.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_connected_worker_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  section text, item text, description text, service_id text,
  monthly_fee text, dependencies text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_connected_worker_usage_rate_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  item text, description text, service_id text, usage_rate text,
  extras jsonb
);

-- Cellular Devices Catalogue book. Mirrors the old
-- raw_telus_cellular_device_pricebook exactly; type_of_service was a
-- constant 'Device Catalogue' in the old file, hardcoded back in here.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_cellular_device_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  device_name text, device_price text, type_of_service text,
  extras jsonb
);

-- New catalogue, no old precedent: wearable/satellite hardware and
-- accessories supporting the Connected Worker Solution sheet.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_connected_worker_hardware_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  item text, description text, service_id text, price text, dependencies text,
  extras jsonb
);

-- Voice and Data book. "Data & Voice Fees" is one sheet with a Service
-- Category column ('Data'/'Voice'); split into these two tables to mirror
-- the old raw_telus_data_services_pricebook / raw_telus_voice_services_pricebook
-- boundary (those were two separate old files, identical column shape).
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_data_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service_category text, service_id text, service_name text,
  short_service_description text, monthly_fee text, ecf_rate text, service_sla text,
  technical_services_support text, ordering_lead_times_objectives text,
  delivery_lead_times_objectives_service_interval text, technical_service_standards text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_voice_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service_category text, service_id text, service_name text,
  short_service_description text, monthly_fee text, ecf_rate text, service_sla text,
  technical_services_support text, ordering_lead_times_objectives text,
  delivery_lead_times_objectives_service_interval text, technical_service_standards text,
  extras jsonb
);

-- Mirrors the old raw_telus_voice_long_distance_fees_pricebook exactly.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_voice_long_distance_fees_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  country text, landline_termination_cpm_rate text, mobile_termination_cpm_rate text,
  extras jsonb
);

-- New catalogue, no old precedent: usage/CPM rates for toll-free, SIP
-- trunking, long distance, and ice Contact Centre features that moved out
-- of the old voice_services catalogue (they're usage-based, not flat
-- monthly fees). id_type/rate_type record which of the sheet's six
-- repeating header variants a row's block used.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_voice_data_usage_rates_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  id_type text, service_id text, service text, description text, rate_type text, rate text,
  extras jsonb
);

-- Time Limited Services book. No old raw_telus_* table exists for any of
-- these 8 sheets (the old schema never had a Time Limited Services
-- pricebook file). All 8 share this one table; `product` names which sheet
-- a row came from, and columns unused by a given sheet are NULL there (e.g.
-- overage_charges/id_type are SIPA-V1-only). "Service ID/ Billing ID" and
-- SIPA's "Service ID" both land in service_id (same concept, different
-- header wording per sheet, never both present on one sheet).
--
-- SIPA V1 has a second, real service ID (Monthly Top Up) on 5 of its 15
-- rows — an alternate billing code for the same add-on, not a separately
-- priced item. Unpivoted so both IDs are independently queryable rows.
-- id_type: 'base' | 'monthly_top_up'. The top-up row's monthly_fee is left
-- NULL (this sheet has no distinct price for it); overage_charges carries
-- over unchanged since that rate applies to the add-on either way.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_tls_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  product text, service_category text, service_name text, service_id text, id_type text,
  short_service_description text, monthly_fee text, overage_charges text,
  extras jsonb
);

-- Professional Services book. Old raw_telus_data_professional_services_pricebook
-- and raw_telus_voice_professional_services_pricebook had identical
-- (title, service_id) key sets — duplicate copies of the same catalogue,
-- not a genuine data/voice split (confirmed against the real old files).
-- The new workbook consolidates them into one sheet, so this merges into
-- one new table too.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_professional_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  professional_service_category text, title text, service_supported text, service_id text,
  business_hours_rate_hourly text, after_business_hours_rate_hourly text,
  extras jsonb
);

-- New catalogue, no old precedent: one-time setup/activation fees
-- supporting the Connected Worker family from the Cellular Services v2.0
-- book (Connected Worker Solution / Hardware / Usage Rate).
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_telus_v2_connected_worker_professional_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  item text, description text, service_id text, rate text, dependencies text,
  extras jsonb
);

-- Rogers (RCCI) pricebook v2 workbooks. Mirrors the old
-- raw_data.raw_rogers_cellular_pricebook exactly (same 11 fields) — the old
-- table was built from cellular.pdf, this is the same catalogue sent as an
-- Excel workbook instead. Monthly Fixed Fee / RLH overage fees are all
-- zeroed in the source file (RCCI masked pricing before sending it), same
-- situation as several of the Telus v2 books above.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_rogers_v2_cellular_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service_id text, service_name text, service_component text,
  speed_mbps_or_capacity_mb text, monthly_fixed_fee text, ecf_rate text,
  rlh_roam_like_home_usa_overage_fee text, rlh_roam_like_home_intl_overage_fee text,
  ecf_unit_of_measure text, fixed_fee text, overage_charge text,
  extras jsonb
);

-- New catalogue, no old table precedent — Rogers pricebook ingestion never
-- had a device catalogue feed before this. Price is zeroed on every row,
-- same masking as raw_rogers_v2_cellular_pricebook above.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_rogers_v2_cellular_device_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  status text, service_id text, device_name text, type text, brand text,
  model text, series text, trim text, capacity text, color text, price text,
  extras jsonb
);

-- Mirrors the old raw_data.raw_rogers_data_pricebook exactly (same 7
-- fields) — the old table was built from data.pdf, this is the same
-- catalogue sent as an Excel workbook instead. Monthly Fixed Fee is zeroed
-- in the source file, same masking as raw_rogers_v2_cellular_pricebook.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_rogers_v2_data_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  service_id text, service_name text, service_component text,
  speed_mbps_or_capacity_mb text, monthly_fixed_fee text, ecf_rate text,
  ecf_unit_of_measure text,
  extras jsonb
);

-- Mirrors the old raw_data.raw_rogers_voice_pricebook exactly (same 10
-- fields, including voice_table_section) — the old table held voice.pdf's
-- two tables (base_service, long_distance) together; this workbook's
-- "Voice Services" and "Long Distance Rates" sheets are the same two
-- tables, fanned into this one table the same way.
--
-- NOT fully masked like the other RCCI v2 tables: "Voice Services" row
-- AV_P_A ("Advantage Voice Analog") carries a real price ($0.95 per
-- Account) — every other row across both sheets is $0.00 / "No Charge" /
-- blank.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_rogers_v2_voice_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  voice_table_section text NOT NULL DEFAULT 'base_service',
  service_id text, service_name text, service_subcategory text, service_component text,
  monthly_fixed_fee text, cpm_rate text, terminating_country text,
  ecf_rate text, ecf_unit_of_measure text,
  extras jsonb
);

-- Mirrors the old raw_data.raw_rogers_professional_services_pricebook
-- exactly (same 7 fields) — the old table was built from
-- professional_services.pdf, this is the same catalogue sent as an Excel
-- workbook instead. Unlike the other RCCI v2 tables, pricing here is NOT
-- masked (real rates). Source workbook's other tabs (TO Change Log, S&U
-- Price Book, S&U Gap Analysis) are a QC comparison report, not pricebook
-- data, and are not ingested.
CREATE TABLE IF NOT EXISTS raw_data_v2.raw_rogers_v2_professional_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  excel_row_number integer,
  title text, services_supported text, service_id text,
  business_hours_rate_hourly text, after_business_hours_rate_hourly text,
  minimum_billing_increment text, fixed_fee text,
  extras jsonb
);
