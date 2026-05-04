-- TSMA cost extracts — raw landing. Run:
--   psql "$DATABASE_URL" -f local_dev/raw_ingestion/tsma_postgres_ingest/schema.sql
--
-- Uses tsma_ingestion_run (separate from NGTA ingestion_run) so CHECK constraints stay independent.

CREATE SCHEMA IF NOT EXISTS raw_data;

CREATE TABLE IF NOT EXISTS raw_data.tsma_ingestion_run (
  tsma_ingestion_run_id   bigserial PRIMARY KEY,
  feed_code               text NOT NULL CHECK (feed_code IN (
    'tsma_wireless', 'tsma_wireline', 'tsma_lite_wireless', 'tsma_lite_wireline', 'tsma_master'
  )),
  source_object_uri       text,
  source_period           date,
  started_at              timestamptz NOT NULL DEFAULT now(),
  finished_at             timestamptz,
  status                  text NOT NULL DEFAULT 'running',
  row_counts_raw          jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_ingestion_run_feed ON raw_data.tsma_ingestion_run (feed_code);

CREATE TABLE IF NOT EXISTS raw_data.tsma_wireless (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
  month_id                  integer,
  month_start_dt            date,
  ccyymm                    text,
  year_num                  integer,
  billg_system_cd           text,
  billg_acct_cd             text,
  billg_acct_nm             text,
  rcid                      text,
  rcid_cust_nm              text,
  cbu_cid                   text,
  cbucid_cust_nm            text,
  lcd_cust_cd               text,
  lcd_category              text,
  lob                       text,
  create_dt                 date,
  total                     text,
  charge_type               text,
  charge_sub_type           text,
  lcd_flg                   text,
  billed_amt                numeric(19,4),
  reason_desc               text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_wireless_ingestion ON raw_data.tsma_wireless (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_lite_wireless (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
  month_id                  integer,
  month_start_dt            date,
  ccyymm                    text,
  year_num                  integer,
  billg_system_cd           text,
  billg_acct_cd             text,
  billg_acct_nm             text,
  rcid                      text,
  rcid_cust_nm              text,
  cbu_cid                   text,
  cbucid_cust_nm            text,
  lcd_cust_cd               text,
  lcd_category              text,
  lob                       text,
  create_dt                 date,
  total                     text,
  charge_type               text,
  charge_sub_type           text,
  lcd_flg                   text,
  billed_amt                numeric(19,4),
  reason_desc               text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_lite_wireless_ingestion ON raw_data.tsma_lite_wireless (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_wireline (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
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
  rn_1                      text,
  rn_2                      text,
  rn_3                      text,
  rn_4                      text,
  epp3_desc                 text,
  epp3_cd                   text,
  quantity                  numeric,
  billed_amt                numeric(19,4),
  line_comment              text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_wireline_ingestion ON raw_data.tsma_wireline (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_lite_wireline (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
  ccyymm                    text,
  year_num                  integer,
  rcid                      text,
  rcid_cust_nm              text,
  cbu_cid                   text,
  cbucid_cust_nm            text,
  tsma_spend_ind            text,
  data_exclusion_flg        text,
  tsma_service_tower        text,
  bpi_prod_desc             text,
  quantity                  numeric,
  billed_amt                numeric(19,4),
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_lite_wireline_ingestion ON raw_data.tsma_lite_wireline (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_ivr (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
  ccyymm                    text,
  year_num                  integer,
  rcid                      text,
  rcid_cust_nm              text,
  billed_amt                numeric(19,4),
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_tsma_ivr_ingestion ON raw_data.tsma_ivr (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.tsma_mms (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.tsma_ingestion_run (tsma_ingestion_run_id),
  ccyymm                    text,
  year_num                  integer,
  entity_name               text,
  total                     numeric(19,4)
);

CREATE INDEX IF NOT EXISTS idx_tsma_mms_ingestion ON raw_data.tsma_mms (ingestion_run_id);
