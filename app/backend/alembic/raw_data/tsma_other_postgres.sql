-- TSMA Other (managed security / router) — raw landing (Alembic 002_raw_data_schema).
-- Apply: cd app/backend && alembic upgrade head
--
-- WLAN / Wi‑Fi wireline-shaped TSMA rows use tsma_wireline + core tsma ingest (tsma/wireline/), not this module.
--
-- Separate tsma_other_ingestion_run from tsma_ingestion_run for independent lineage.
--
-- If you previously applied a schema with tsma_other_managed_wlan_wifi, drop that table and
-- alter the feed_code CHECK to remove 'tsma_other_managed_wlan_wifi' (constraint name may vary:
-- \d raw_data.tsma_other_ingestion_run in psql).

CREATE SCHEMA IF NOT EXISTS raw_data;

CREATE TABLE IF NOT EXISTS raw_data.tsma_other_ingestion_run (
  tsma_other_ingestion_run_id  bigserial PRIMARY KEY,
  feed_code                    text NOT NULL CHECK (feed_code IN (
    'tsma_other_managed_security',
    'tsma_other_managed_router'
  )),
  source_object_uri            text,
  source_period                date,
  started_at                   timestamptz NOT NULL DEFAULT now(),
  finished_at                  timestamptz,
  status                       text NOT NULL DEFAULT 'running',
  row_counts_raw               jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_other_ingestion_run_feed
  ON raw_data.tsma_other_ingestion_run (feed_code);

-- Same wireline-shaped columns as tsma_wireline.

CREATE TABLE IF NOT EXISTS raw_data.tsma_other_managed_security (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_other_ingestion_run (tsma_other_ingestion_run_id),
  month_id                  integer,
  month_start_dt            date,
  ccyymm                    text,
  year_num                  integer,
  lob                       text,
  lcd_cust_cd               text,
  entity                    text,
  billg_system_cd           text,
  rcid                      text,
  rcid_cust_nm              text,
  cbu_cid                   text,
  cbucid_cust_nm            text,
  tsma_spend_ind            text,
  data_exclusion_flg        text,
  tsma_service_tower        text,
  sap_mic_cd_flg            text,
  sap_mic_cd                text,
  bpi_prod_cd               text,
  bpi_prod_desc             text,
  prod_family_cd            text,
  prod_family_desc          text,
  rn_1                      numeric,
  rn_2                      numeric,
  rn_3                      numeric,
  rn_4                      numeric,
  epp3_desc                 text,
  epp3_cd                   text,
  quantity                  numeric,
  billed_amt                numeric(19,4),
  line_comment              text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_other_managed_security_ingestion
  ON raw_data.tsma_other_managed_security (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_other_managed_router (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_other_ingestion_run (tsma_other_ingestion_run_id),
  month_id                  integer,
  month_start_dt            date,
  ccyymm                    text,
  year_num                  integer,
  lob                       text,
  lcd_cust_cd               text,
  entity                    text,
  billg_system_cd           text,
  rcid                      text,
  rcid_cust_nm              text,
  cbu_cid                   text,
  cbucid_cust_nm            text,
  tsma_spend_ind            text,
  data_exclusion_flg        text,
  tsma_service_tower        text,
  sap_mic_cd_flg            text,
  sap_mic_cd                text,
  bpi_prod_cd               text,
  bpi_prod_desc             text,
  prod_family_cd            text,
  prod_family_desc          text,
  rn_1                      numeric,
  rn_2                      numeric,
  rn_3                      numeric,
  rn_4                      numeric,
  epp3_desc                 text,
  epp3_cd                   text,
  quantity                  numeric,
  billed_amt                numeric(19,4),
  line_comment              text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_other_managed_router_ingestion
  ON raw_data.tsma_other_managed_router (ingestion_run_id);
