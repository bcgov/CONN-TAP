# Glue catalog (Athena) external tables — created as part of Terraform deployment.
# Databases: ngta_telecom, tsma_telecom_qsr (from glue_catalog.tf).

resource "aws_glue_catalog_table" "telus_spend" {
  name          = "telus_spend"
  database_name = aws_glue_catalog_database.ngta_telecom.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${var.ngta_raw_bucket_name}/processed/telus/spend_reports/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "account number"
      type = "string"
    }
    columns {
      name = "account description"
      type = "string"
    }
    columns {
      name = "service number"
      type = "string"
    }
    columns {
      name = "statement date"
      type = "string"
    }
    columns {
      name = "due date"
      type = "string"
    }
    columns {
      name = "statement section"
      type = "string"
    }
    columns {
      name = "organization"
      type = "string"
    }
    columns {
      name = "statement category"
      type = "string"
    }
    columns {
      name = "statement sub category"
      type = "string"
    }
    columns {
      name = "record type description"
      type = "string"
    }
    columns {
      name = "amount"
      type = "string"
    }
    columns {
      name = "bill section"
      type = "string"
    }
    columns {
      name = "detail description"
      type = "string"
    }
    columns {
      name = "invoice number"
      type = "string"
    }
    columns {
      name = "month"
      type = "string"
    }
    columns {
      name = "service address"
      type = "string"
    }
    columns {
      name = "service description"
      type = "string"
    }
    columns {
      name = "source"
      type = "string"
    }
    columns {
      name = "source id"
      type = "string"
    }
    columns {
      name = "entity_name"
      type = "string"
    }
    columns {
      name = "service location id"
      type = "string"
    }
    columns {
      name = "ingestion_year"
      type = "string"
    }
    columns {
      name = "ingestion_month"
      type = "string"
    }
    columns {
      name = "ingestion_ts"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "rogers_spend" {
  name          = "rogers_spend"
  database_name = aws_glue_catalog_database.ngta_telecom.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${var.ngta_raw_bucket_name}/processed/rogers/spend_reports/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "invoice_date"
      type = "string"
    }
    columns {
      name = "company_code"
      type = "string"
    }
    columns {
      name = "bge"
      type = "string"
    }
    columns {
      name = "curr_root_ban"
      type = "string"
    }
    columns {
      name = "customer_ban"
      type = "string"
    }
    columns {
      name = "subscriber_no"
      type = "string"
    }
    columns {
      name = "username"
      type = "string"
    }
    columns {
      name = "price_plan"
      type = "string"
    }
    columns {
      name = "plan_description"
      type = "string"
    }
    columns {
      name = "service_id"
      type = "string"
    }
    columns {
      name = "data_plan"
      type = "string"
    }
    columns {
      name = "data_plan_description"
      type = "string"
    }
    columns {
      name = "service_id_2"
      type = "string"
    }
    columns {
      name = "init_activation_date"
      type = "string"
    }
    columns {
      name = "deactivation_date"
      type = "string"
    }
    columns {
      name = "commit_start_date"
      type = "string"
    }
    columns {
      name = "commit_end_date"
      type = "string"
    }
    columns {
      name = "commit_orig_no_month"
      type = "string"
    }
    columns {
      name = "line_type"
      type = "string"
    }
    columns {
      name = "dept_code"
      type = "string"
    }
    columns {
      name = "dept_desc"
      type = "string"
    }
    columns {
      name = "sim"
      type = "string"
    }
    columns {
      name = "imei"
      type = "string"
    }
    columns {
      name = "device"
      type = "string"
    }
    columns {
      name = "data_overage"
      type = "string"
    }
    columns {
      name = "sms_domestic"
      type = "string"
    }
    columns {
      name = "sms_intl"
      type = "string"
    }
    columns {
      name = "sms_us"
      type = "string"
    }
    columns {
      name = "ld_intl"
      type = "string"
    }
    columns {
      name = "ld_us"
      type = "string"
    }
    columns {
      name = "ecf_data"
      type = "string"
    }
    columns {
      name = "ecf_voice"
      type = "string"
    }
    columns {
      name = "hardware"
      type = "string"
    }
    columns {
      name = "msf_flex_data_options"
      type = "string"
    }
    columns {
      name = "msf_other_options"
      type = "string"
    }
    columns {
      name = "msf_other_plans"
      type = "string"
    }
    columns {
      name = "msf_pool_share_data_options"
      type = "string"
    }
    columns {
      name = "msf_standalone_data_options"
      type = "string"
    }
    columns {
      name = "msf_voice_and_data_plan"
      type = "string"
    }
    columns {
      name = "msf_voice_plan"
      type = "string"
    }
    columns {
      name = "non_spending_adj"
      type = "string"
    }
    columns {
      name = "intl_roaming_data"
      type = "string"
    }
    columns {
      name = "intl_roam_like_home"
      type = "string"
    }
    columns {
      name = "intl_roaming_addons"
      type = "string"
    }
    columns {
      name = "roaming_adj"
      type = "string"
    }
    columns {
      name = "us_roaming_data"
      type = "string"
    }
    columns {
      name = "us_roam_like_home"
      type = "string"
    }
    columns {
      name = "us_roaming_addons"
      type = "string"
    }
    columns {
      name = "push_to_talk"
      type = "string"
    }
    columns {
      name = "others"
      type = "string"
    }
    columns {
      name = "billed_amount(pre-tax)"
      type = "string"
    }
    columns {
      name = "gst"
      type = "string"
    }
    columns {
      name = "pst"
      type = "string"
    }
    columns {
      name = "hst"
      type = "string"
    }
    columns {
      name = "qst"
      type = "string"
    }
    columns {
      name = "billed_amount(post-tax)"
      type = "string"
    }
    columns {
      name = "remaining_device_recovery_fee"
      type = "string"
    }
    columns {
      name = "voice_domestic_usage"
      type = "string"
    }
    columns {
      name = "voice_rlh_us_usage"
      type = "string"
    }
    columns {
      name = "voice_rlh_intl_usage"
      type = "string"
    }
    columns {
      name = "voice_others_usage"
      type = "string"
    }
    columns {
      name = "data_domestic_usage"
      type = "string"
    }
    columns {
      name = "data_rlh_us_usage"
      type = "string"
    }
    columns {
      name = "data_rlh_intl_usage"
      type = "string"
    }
    columns {
      name = "data_others_usage"
      type = "string"
    }
    columns {
      name = "sms_domestic_usage"
      type = "string"
    }
    columns {
      name = "sms_rlh_us_usage"
      type = "string"
    }
    columns {
      name = "sms_rlh_intl_usage"
      type = "string"
    }
    columns {
      name = "sms_others_usage"
      type = "string"
    }
    columns {
      name = "data_soc"
      type = "string"
    }
    columns {
      name = "data_soc_description"
      type = "string"
    }
    columns {
      name = "city"
      type = "string"
    }
    columns {
      name = "sub-bge"
      type = "string"
    }
    columns {
      name = "entity_name"
      type = "string"
    }
    columns {
      name = "ingestion_year"
      type = "string"
    }
    columns {
      name = "ingestion_month"
      type = "string"
    }
    columns {
      name = "ingestion_ts"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "cellular_qsr" {
  name          = "cellular_qsr"
  database_name = aws_glue_catalog_database.tsma_telecom_qsr.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${var.tsma_raw_bucket_name}/processed_quarterly_spend_report/latest/wls/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "monthid"
      type = "string"
    }
    columns {
      name = "monthstartdt"
      type = "string"
    }
    columns {
      name = "ccyymm"
      type = "string"
    }
    columns {
      name = "yearnum"
      type = "string"
    }
    columns {
      name = "billgsystemcd"
      type = "string"
    }
    columns {
      name = "billgacctcd"
      type = "string"
    }
    columns {
      name = "billgacctnm"
      type = "string"
    }
    columns {
      name = "rcid"
      type = "string"
    }
    columns {
      name = "rcid_cust_nm"
      type = "string"
    }
    columns {
      name = "cbu_cid"
      type = "string"
    }
    columns {
      name = "cbucid_cust_nm"
      type = "string"
    }
    columns {
      name = "lcdcustcd"
      type = "string"
    }
    columns {
      name = "lcdcategory"
      type = "string"
    }
    columns {
      name = "lob"
      type = "string"
    }
    columns {
      name = "createdt"
      type = "string"
    }
    columns {
      name = "total"
      type = "string"
    }
    columns {
      name = "chargetype"
      type = "string"
    }
    columns {
      name = "chargesubtype"
      type = "string"
    }
    columns {
      name = "lcd_flg"
      type = "string"
    }
    columns {
      name = "billedamt"
      type = "string"
    }
    columns {
      name = "reasondesc"
      type = "string"
    }
    columns {
      name = "ingestion_year"
      type = "string"
    }
    columns {
      name = "ingestion_quarter"
      type = "string"
    }
    columns {
      name = "domain"
      type = "string"
    }
    columns {
      name = "ingestion_ts"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "voice_qsr" {
  name          = "voice_qsr"
  database_name = aws_glue_catalog_database.tsma_telecom_qsr.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${var.tsma_raw_bucket_name}/processed_quarterly_spend_report/latest/wln/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "monthid"
      type = "string"
    }
    columns {
      name = "monthstartdt"
      type = "string"
    }
    columns {
      name = "ccyymm"
      type = "string"
    }
    columns {
      name = "yearnum"
      type = "string"
    }
    columns {
      name = "lob"
      type = "string"
    }
    columns {
      name = "lcdcustcd"
      type = "string"
    }
    columns {
      name = "entity"
      type = "string"
    }
    columns {
      name = "billgsystemcd"
      type = "string"
    }
    columns {
      name = "rcid"
      type = "string"
    }
    columns {
      name = "rcid_cust_nm"
      type = "string"
    }
    columns {
      name = "cbu_cid"
      type = "string"
    }
    columns {
      name = "cbucid_cust_nm"
      type = "string"
    }
    columns {
      name = "tsma_spend_ind"
      type = "string"
    }
    columns {
      name = "dataexclusion_flg"
      type = "string"
    }
    columns {
      name = "tsma_service_tower"
      type = "string"
    }
    columns {
      name = "sap_mic_cd_flg"
      type = "string"
    }
    columns {
      name = "sap_mic_cd"
      type = "string"
    }
    columns {
      name = "bpi_prod_cd"
      type = "string"
    }
    columns {
      name = "bpi_prod_desc"
      type = "string"
    }
    columns {
      name = "prod_family_cd"
      type = "string"
    }
    columns {
      name = "prod_family_desc"
      type = "string"
    }
    columns {
      name = "rn_1"
      type = "string"
    }
    columns {
      name = "rn_2"
      type = "string"
    }
    columns {
      name = "rn_3"
      type = "string"
    }
    columns {
      name = "rn_4"
      type = "string"
    }
    columns {
      name = "epp3_desc"
      type = "string"
    }
    columns {
      name = "epp3_cd"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "string"
    }
    columns {
      name = "billedamt"
      type = "string"
    }
    columns {
      name = "comment"
      type = "string"
    }
    columns {
      name = "ingestion_year"
      type = "string"
    }
    columns {
      name = "ingestion_quarter"
      type = "string"
    }
    columns {
      name = "domain"
      type = "string"
    }
    columns {
      name = "ingestion_ts"
      type = "string"
    }
  }
}
