-- NGTA pricebook raw landing. Run:
--   psql "$DATABASE_URL" -f local_dev/raw_ingestion/ngta_pricebooks_ingest/schema.sql

CREATE SCHEMA IF NOT EXISTS raw_data;

CREATE TABLE IF NOT EXISTS raw_data.pricebook_ingestion_run (
  pricebook_ingestion_run_id bigserial PRIMARY KEY,
  provider                   text NOT NULL CHECK (provider IN ('telus', 'rogers')),
  pricebook_feed             text NOT NULL,
  source_object_uri          text,
  source_period              date,
  started_at                 timestamptz NOT NULL DEFAULT now(),
  finished_at                timestamptz,
  status                     text NOT NULL DEFAULT 'running',
  row_counts_raw             jsonb
);

CREATE INDEX IF NOT EXISTS idx_pricebook_ingestion_provider_feed
  ON raw_data.pricebook_ingestion_run (provider, pricebook_feed);

-- Rogers Professional Services pricebook (PDF: professional_services.pdf)
CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_professional_services_pricebook (
  raw_id                         bigserial PRIMARY KEY,
  pricebook_ingestion_run_id     bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  pdf_page_number                integer,
  title                          text,
  services_supported             text,
  service_id                     text,
  business_hours_rate_hourly     text,
  after_business_hours_rate_hourly text,
  minimum_billing_increment      text,
  fixed_fee                      text,
  extras                         jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_prof_services_ingestion
  ON raw_data.raw_rogers_professional_services_pricebook (pricebook_ingestion_run_id);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_prof_services_service_id
  ON raw_data.raw_rogers_professional_services_pricebook (service_id);

-- Rogers Data pricebook (PDF: data.pdf)
CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_data_pricebook (
  raw_id                     bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  pdf_page_number            integer,
  service_id                 text,
  service_name               text,
  service_component          text,
  speed_mbps_or_capacity_mb  text,
  monthly_fixed_fee          text,
  ecf_rate                   text,
  ecf_unit_of_measure        text,
  extras                     jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_data_ingestion
  ON raw_data.raw_rogers_data_pricebook (pricebook_ingestion_run_id);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_data_service_id
  ON raw_data.raw_rogers_data_pricebook (service_id);

-- Rogers Cellular pricebook (PDF: cellular.pdf)
CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_cellular_pricebook (
  raw_id                                bigserial PRIMARY KEY,
  pricebook_ingestion_run_id            bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  pdf_page_number                       integer,
  service_id                            text,
  service_name                          text,
  service_component                     text,
  speed_mbps_or_capacity_mb             text,
  monthly_fixed_fee                     text,
  ecf_rate                              text,
  rlh_roam_like_home_usa_overage_fee    text,
  rlh_roam_like_home_intl_overage_fee   text,
  ecf_unit_of_measure                   text,
  fixed_fee                             text,
  overage_charge                        text,
  extras                                jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_cellular_ingestion
  ON raw_data.raw_rogers_cellular_pricebook (pricebook_ingestion_run_id);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_cellular_service_id
  ON raw_data.raw_rogers_cellular_pricebook (service_id);

-- Rogers Voice pricebook (PDF: voice.pdf; may contain multiple table sections)
CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_voice_pricebook (
  raw_id                     bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  pdf_page_number            integer,
  voice_table_section        text NOT NULL DEFAULT 'base_service',
  service_id                 text,
  service_name               text,
  service_subcategory        text,
  service_component          text,
  monthly_fixed_fee          text,
  cpm_rate                   text,
  terminating_country        text,
  ecf_rate                   text,
  ecf_unit_of_measure        text,
  extras                     jsonb
);

-- If the voice table already exists from an earlier schema version:
ALTER TABLE raw_data.raw_rogers_voice_pricebook
  ADD COLUMN IF NOT EXISTS service_subcategory text,
  ADD COLUMN IF NOT EXISTS terminating_country text;

UPDATE raw_data.raw_rogers_voice_pricebook
SET voice_table_section = 'base_service'
WHERE voice_table_section = 'contact_center';

CREATE INDEX IF NOT EXISTS idx_raw_rogers_voice_ingestion
  ON raw_data.raw_rogers_voice_pricebook (pricebook_ingestion_run_id);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_voice_service_id
  ON raw_data.raw_rogers_voice_pricebook (service_id);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_voice_section
  ON raw_data.raw_rogers_voice_pricebook (voice_table_section);

-- Telus pricebook catalogues (Excel: u_ngta_*.xlsx under price_books/telus/)

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_additional_fees_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  service text, fee text, cpm_rate text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_catalog_and_price_list_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  category text, fee_based_optional_features text, service_id text, monthly_fee text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_device_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  device_name text, device_price text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_long_distance_cost_per_minute_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  calling_to text, cpm_rate text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_mms_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  service text, service_id text, monthly_fee text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_roaming_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  roaming text, fee text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_cellular_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  category text, rate_plan text, service_id text, monthly_fee text, type_of_service text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_control_center_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  category text, rate_plan text, service_id text, monthly_fee text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_data_professional_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  professional_service_category text, title text, service_supported text,
  service_id text, business_hours_rate_hourly text, after_business_hours_rate_hourly text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_data_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  service_category text, service_id text, service_name text,
  short_service_description text, monthly_fee text, ecf_rate text, service_sla text,
  technical_services_support text, ordering_lead_times_objectives text,
  delivery_lead_times_objectives_service_interval text, technical_service_standards text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_voice_long_distance_fees_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  country text, landline_termination_cpm_rate text, mobile_termination_cpm_rate text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_voice_professional_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  professional_service_category text, title text, service_supported text,
  service_id text, business_hours_rate_hourly text, after_business_hours_rate_hourly text,
  extras jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_voice_services_pricebook (
  raw_id bigserial PRIMARY KEY,
  pricebook_ingestion_run_id bigint NOT NULL
    REFERENCES raw_data.pricebook_ingestion_run (pricebook_ingestion_run_id),
  sheet_name text,
  service_category text, service_id text, service_name text,
  short_service_description text, monthly_fee text, ecf_rate text, service_sla text,
  technical_services_support text, ordering_lead_times_objectives text,
  delivery_lead_times_objectives_service_interval text, technical_service_standards text,
  extras jsonb
);
