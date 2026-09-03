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
