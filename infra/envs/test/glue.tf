resource "aws_glue_job" "rogers_spend_ingestion" {
  name     = "rogers_spend_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.glue_assets_bucket}/scripts/rogers_spend_ingestion.py"
  }

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
}

resource "aws_glue_job" "telus_spend_ingestion" {
  name     = "telus_spend_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.glue_assets_bucket}/scripts/telus_spend_ingestion.py"
  }

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
}

resource "aws_glue_job" "telus_quantities_ingestion" {
  name     = "telus_quantities_ingestion"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.glue_assets_bucket}/scripts/telus_quantities_ingestion.py"
  }

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  timeout           = 480
}


resource "aws_glue_job" "load_ngta_rogers_pricebook_notebook" {
  name     = "load-ngta-rogers-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/load-ngta-rogers-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "load_ngta_telus_pricebook_notebook" {
  name     = "load-ngta-telus-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/load-ngta-telus-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "load_tsma_pricebook_notebook" {
  name     = "load-tsma-pricebook-notebook"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/load-tsma-pricebook-notebook.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "mapping_to_master" {
  name     = "mapping-to-master"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/mapping-to-master.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "move_tsma_files" {
  name     = "move_tsma_files"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/move_tsma_files.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "ngta_rogers_fact" {
  name     = "ngta-rogers-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/ngta-rogers-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "ngta_telus_fact" {
  name     = "ngta-telus-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/ngta-telus-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_fact" {
  name     = "tsma-fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/tsma-fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_service_dashboard_data" {
  name     = "tsma-service-dashboard-data"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/tsma-service-dashboard-data.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}

resource "aws_glue_job" "tsma_fact_underscore" {
  name     = "tsma_fact"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_assets_bucket}/scripts/tsma_fact.py"
    python_version  = "3"
  }

  lifecycle { ignore_changes = all }
}