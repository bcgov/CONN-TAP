-- NGTA raw landing. Run:
--   psql "$DATABASE_URL" -f local_dev/raw_ingestion/ngta_postgres_ingest/schema.sql
--
-- If you already have raw_rogers_spend from an older version:
--   ALTER TABLE raw_data.raw_rogers_spend RENAME TO raw_rogers_spend_cellular;
--   ALTER INDEX raw_data.idx_raw_rogers_ingestion RENAME TO idx_raw_rogers_cellular_ingestion;
-- If you have raw_rogers_spend_voice from a prior ingest:
--   ALTER TABLE raw_data.raw_rogers_spend_voice RENAME TO raw_rogers_spend_data_voice;
--   ALTER INDEX raw_data.idx_raw_rogers_voice_ingestion RENAME TO idx_raw_rogers_data_voice_ingestion;

CREATE SCHEMA IF NOT EXISTS raw_data;

CREATE TABLE IF NOT EXISTS raw_data.ingestion_run (
  ingestion_run_id   bigserial PRIMARY KEY,
  provider           text NOT NULL CHECK (provider IN ('telus', 'rogers')),
  source_object_uri  text,
  source_period      date,
  started_at         timestamptz NOT NULL DEFAULT now(),
  finished_at        timestamptz,
  status             text NOT NULL DEFAULT 'running',
  row_counts_raw     jsonb
);

CREATE TABLE IF NOT EXISTS raw_data.raw_telus_spend (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.ingestion_run (ingestion_run_id),
  sheet_name                text,
  account_number            text,
  account_description       text,
  service_number            text,
  statement_date            date,
  due_date                  date,
  statement_section         text,
  organization              text,
  statement_category        text,
  statement_sub_category    text,
  record_type_description   text,
  amount                    numeric(19,4),
  bill_section              text,
  detail_description        text,
  invoice_number            text,
  month                     text,
  service_address           text,
  service_description       text,
  source                    text,
  source_id                 text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_telus_ingestion ON raw_data.raw_telus_spend (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_spend_cellular (
  raw_id                   bigserial PRIMARY KEY,
  ingestion_run_id         bigint NOT NULL REFERENCES raw_data.ingestion_run (ingestion_run_id),
  invoice_date             date,
  company_code             text,
  bge                      text,
  curr_root_ban            text,
  customer_ban             text,
  subscriber_no            text,
  username                 text,
  price_plan               text,
  plan_description         text,
  service_id               text,
  data_plan                text,
  data_plan_description    text,
  service_id_2             text,
  init_activation_date     date,
  deactivation_date        date,
  commit_start_date        date,
  commit_end_date          date,
  commit_orig_no_month     numeric,
  line_type                text,
  dept_code                text,
  dept_desc                text,
  sim                      text,
  imei                     text,
  device                   text,
  data_overage             numeric(19,4),
  sms_domestic             numeric(19,4),
  sms_intl                 numeric(19,4),
  sms_us                   numeric(19,4),
  ld_intl                  numeric(19,4),
  ld_us                    numeric(19,4),
  ecf_data                 numeric(19,4),
  ecf_voice                numeric(19,4),
  hardware                 numeric(19,4),
  msf_flex_data_options    numeric(19,4),
  msf_other_options        numeric(19,4),
  msf_other_plans          numeric(19,4),
  msf_pool_share_data_options numeric(19,4),
  msf_standalone_data_options numeric(19,4),
  msf_voice_and_data_plan  numeric(19,4),
  msf_voice_plan           numeric(19,4),
  non_spending_adj         numeric(19,4),
  intl_roaming_data        numeric(19,4),
  intl_roam_like_home      numeric(19,4),
  intl_roaming_addons      numeric(19,4),
  roaming_adj              numeric(19,4),
  us_roaming_data          numeric(19,4),
  us_roam_like_home        numeric(19,4),
  us_roaming_addons        numeric(19,4),
  push_to_talk             numeric(19,4),
  others                   numeric(19,4),
  billed_amount_pre_tax    numeric(19,4),
  gst                      numeric(19,4),
  pst                      numeric(19,4),
  hst                      numeric(19,4),
  qst                      numeric(19,4),
  billed_amount_post_tax   numeric(19,4),
  remaining_device_recovery_fee numeric(19,4),
  voice_domestic_usage     numeric,
  voice_rlh_us_usage       numeric,
  voice_rlh_intl_usage     numeric,
  voice_others_usage       numeric,
  data_domestic_usage      numeric,
  data_rlh_us_usage        numeric,
  data_rlh_intl_usage      numeric,
  data_others_usage        numeric,
  sms_domestic_usage       numeric,
  sms_rlh_us_usage         numeric,
  sms_rlh_intl_usage       numeric,
  sms_others_usage         numeric,
  data_soc                 text,
  data_soc_description     text,
  city                     text,
  sub_bge                  text,
  extras                   jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_cellular_ingestion ON raw_data.raw_rogers_spend_cellular (ingestion_run_id);

CREATE TABLE IF NOT EXISTS raw_data.raw_rogers_spend_data_voice (
  raw_id                    bigserial PRIMARY KEY,
  ingestion_run_id          bigint NOT NULL REFERENCES raw_data.ingestion_run (ingestion_run_id),
  bge                       text,
  sub_bge                   text,
  accountno                 text,
  bpso                      text,
  billingdate               date,
  billingperiod_startdate   date,
  billingperiod_enddate     date,
  circuitno                 text,
  custrefno                 text,
  servicestartdate          date,
  address                   text,
  city                      text,
  province                  text,
  postalcode                text,
  productline               text,
  producttype               text,
  chargetype                text,
  service_id                text,
  charge_description        text,
  service_component         text,
  rate                      numeric,
  quantity                  numeric,
  consumption               numeric,
  billed_amount_pre_tax     numeric(19,4),
  gst                       numeric(19,4),
  pst                       numeric(19,4),
  taxamount                 numeric(19,4),
  totalamount               numeric(19,4),
  originating_tn            text,
  terminating_tn            text,
  destination               text,
  destination_country       text,
  extras                    jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_rogers_data_voice_ingestion ON raw_data.raw_rogers_spend_data_voice (ingestion_run_id);

-- Rogers voice + data share one long-form table raw_rogers_spend_data_voice (voice-shaped columns). No separate raw_rogers_spend_data.
-- If an older DB still has raw_rogers_spend_data: DROP TABLE raw_data.raw_rogers_spend_data;
