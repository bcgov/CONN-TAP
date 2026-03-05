resource "aws_glue_job" "rogers_spend_ingestion" {
  name                    = "rogers_spend_ingestion"
  role_arn                = aws_iam_role.glue_role.arn
  job_run_queuing_enabled = true


  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/rogers_spend_ingestion.py"
    python_version  = "3"
  }

  glue_version      = "5.0"
  execution_class   = "STANDARD"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  default_arguments = {
    "--enable-glue-datacatalog"      = "true"
    "--OUTPUT_BUCKET"                = "ngta-raw-data"
    "--MONTH_NUM"                    = "11"
    "--job-bookmark-option"          = "job-bookmark-disable"
    "--TempDir"                      = "s3://aws-glue-assets-585768151939-ca-central-1/temporary/"
    "--MONTH_NAME"                   = "November"
    "--YEAR"                         = "2025"
    "--enable-metrics"               = "true"
    "--enable-spark-ui"              = "true"
    "--spark-event-logs-path"        = "s3://aws-glue-assets-585768151939-ca-central-1/sparkHistoryLogs/"
    "--enable-job-insights"          = "true"
    "--additional-python-modules"    = "openpyxl==3.1.2"
    "--enable-observability-metrics" = "true"
    "--RAW_BUCKET"                   = "ngta-raw-data"
    "--job-language"                 = "python"
    "--enable-auto-scaling"          = "true"
  }
}

resource "aws_glue_job" "telus_spend_ingestion" {
  name                    = "telus_spend_ingestion"
  role_arn                = aws_iam_role.glue_role.arn
  job_run_queuing_enabled = true

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/telus_spend_ingestion.py"
    python_version  = "3"
  }

  glue_version      = "5.0"
  execution_class   = "STANDARD"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  default_arguments = {
    "--enable-glue-datacatalog"      = "true"
    "--OUTPUT_BUCKET"                = "ngta-raw-data"
    "--MONTH_NUM"                    = "10"
    "--job-bookmark-option"          = "job-bookmark-disable"
    "--TempDir"                      = "s3://aws-glue-assets-585768151939-ca-central-1/temporary/"
    "--MONTH_NAME"                   = "October"
    "--YEAR"                         = "2025"
    "--enable-metrics"               = "true"
    "--enable-spark-ui"              = "true"
    "--spark-event-logs-path"        = "s3://aws-glue-assets-585768151939-ca-central-1/sparkHistoryLogs/"
    "--enable-job-insights"          = "true"
    "--additional-python-modules"    = "openpyxl==3.1.2"
    "--enable-observability-metrics" = "true"
    "--RAW_BUCKET"                   = "ngta-raw-data"
    "--job-language"                 = "python"
  }
}

resource "aws_glue_job" "telus_quantities_ingestion" {
  name                    = "telus_quantities_ingestion"
  role_arn                = aws_iam_role.glue_role.arn
  job_run_queuing_enabled = true

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/telus_quantities_ingestion.py"
    python_version  = "3"
  }

  source_control_details {
    provider = "GITHUB"
    folder   = "telus_quantities_ingestion.py"
  }

  glue_version      = "5.0"
  execution_class   = "STANDARD"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
  max_retries       = 0

  execution_property {
    max_concurrent_runs = 1
  }

  default_arguments = {
    "--REPORT_TYPE"                  = "quantities_reports"
    "--enable-glue-datacatalog"      = "true"
    "--job-bookmark-option"          = "job-bookmark-disable"
    "--PROVIDER"                     = "telus"
    "--TempDir"                      = "s3://aws-glue-assets-585768151939-ca-central-1/temporary/"
    "--BUCKET"                       = "ngta-raw-data"
    "--SOURCE_PREFIX_BASE"           = "raw"
    "--enable-metrics"               = "true"
    "--enable-spark-ui"              = "true"
    "--spark-event-logs-path"        = "s3://aws-glue-assets-585768151939-ca-central-1/sparkHistoryLogs/"
    "--enable-job-insights"          = "true"
    "--additional-python-modules"    = "openpyxl==3.1.2"
    "--enable-observability-metrics" = "true"
    "--OUTPUT_PREFIX_BASE"           = "processed"
    "--job-language"                 = "python"
  }
}

resource "aws_glue_job" "load_ngta_rogers_pricebook_notebook" {
  name     = "load-ngta-rogers-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/load-ngta-rogers-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "load_ngta_telus_pricebook_notebook" {
  name     = "load-ngta-telus-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/load-ngta-telus-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "load_tsma_pricebook_notebook" {
  name     = "load-tsma-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/load-tsma-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "mapping_to_master" {
  name     = "mapping-to-master"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/mapping-to-master.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "move_tsma_files" {
  name     = "move_tsma_files"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/move_tsma_files.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "ngta_rogers_fact" {
  name     = "ngta-rogers-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/ngta-rogers-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "ngta_telus_fact" {
  name     = "ngta-telus-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/ngta-telus-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_fact" {
  name     = "tsma-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/tsma-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_service_dashboard_data" {
  name     = "tsma-service-dashboard-data"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/tsma-service-dashboard-data.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_fact_underscore" {
  name     = "tsma_fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://aws-glue-assets-585768151939-ca-central-1/scripts/tsma_fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}