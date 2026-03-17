resource "aws_glue_job" "load_ngta_rogers_pricebook_notebook" {
  name     = "load-ngta-rogers-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/load-ngta-rogers-pricebook-notebook.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "load_ngta_telus_pricebook_notebook" {
  name     = "load-ngta-telus-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/load-ngta-telus-pricebook-notebook.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "load_tsma_pricebook_notebook" {
  name     = "load-tsma-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/load-tsma-pricebook-notebook.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "mapping_to_master" {
  name     = "mapping-to-master"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/mapping-to-master.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "move_tsma_files" {
  name     = "move_tsma_files"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/move_tsma_files.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "ngta_rogers_fact" {
  name     = "ngta-rogers-fact"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/ngta-rogers-fact.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "ngta_telus_fact" {
  name     = "ngta-telus-fact"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/ngta-telus-fact.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "rogers_spend_ingestion" {
  name     = "rogers_spend_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/rogers_spend_ingestion.py"
    python_version  = "3"
  }

  default_arguments = {
    "--OUTPUT_BUCKET"             = var.ngta_raw_bucket_name
    "--RAW_BUCKET"                = var.ngta_raw_bucket_name
    "--additional-python-modules" = "openpyxl==3.1.2"
    "--enable-glue-datacatalog"   = "true"
    "--job-bookmark-option"       = "job-bookmark-disable"
    "--job-language"              = "python"
  }
}

resource "aws_glue_job" "telus_quantities_ingestion" {
  name     = "telus_quantities_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/telus_quantities_ingestion.py"
    python_version  = "3"
  }

  default_arguments = {
  "--BUCKET"                    = var.ngta_raw_bucket_name
  "--OUTPUT_PREFIX_BASE"        = "processed"
  "--PROVIDER"                  = "telus"
  "--REPORT_TYPE"               = "quantities_reports"
  "--SOURCE_PREFIX_BASE"        = "raw"
  "--additional-python-modules" = "openpyxl==3.1.2"
  "--enable-glue-datacatalog"   = "true"
  "--job-bookmark-option"       = "job-bookmark-disable"
  "--job-language"              = "python"
  }
}

resource "aws_glue_job" "telus_spend_ingestion" {
  name     = "telus_spend_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/telus_spend_ingestion.py"
    python_version  = "3"
  }

  default_arguments = {
  "--OUTPUT_BUCKET"             = var.ngta_raw_bucket_name
  "--RAW_BUCKET"                = var.ngta_raw_bucket_name
  "--additional-python-modules" = "openpyxl==3.1.2"
  "--enable-glue-datacatalog"   = "true"
  "--job-bookmark-option"       = "job-bookmark-disable"
  "--job-language"              = "python"
  }
}

resource "aws_glue_job" "tsma_fact" {
  name     = "tsma-fact"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/tsma-fact.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "tsma_fact_underscore" {
  name     = "tsma_fact"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/tsma_fact.py"
    python_version  = "3"
  }
}

resource "aws_glue_job" "tsma_qsr_ingestion" {
  name     = "tsma_qsr_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/tsma_qsr_ingestion.py"
    python_version  = "3"
  }

  default_arguments = {
  "--OUTPUT_BUCKET"             = var.tsma_raw_bucket_name
  "--RAW_BUCKET"                = var.tsma_raw_bucket_name
  "--additional-python-modules" = "pyarrow==14.0.2,openpyxl==3.1.2"
  "--enable-glue-datacatalog"   = "true"
  "--job-bookmark-option"       = "job-bookmark-disable"
  "--job-language"              = "python"
  }
}

resource "aws_glue_job" "tsma_service_dashboard_data" {
  name     = "tsma-service-dashboard-data"
  role_arn = aws_iam_role.glue_role.arn

  execution_property {
    max_concurrent_runs = var.glue_job_max_concurrent_runs
  }

  command {
    script_location = "s3://${var.glue_assets_bucket_name}/scripts/tsma-service-dashboard-data.py"
    python_version  = "3"
  }
}