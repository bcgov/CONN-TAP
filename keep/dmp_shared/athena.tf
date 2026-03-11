resource "aws_athena_workgroup" "ngta_powerbi" {
  name        = "ngta_powerbi"
  description = "Athena workgroup for NGTA/TSMA Parquet queries (Power BI)."

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    requester_pays_enabled             = false

    result_configuration {
      output_location = "s3://${var.ngta_raw_bucket}/${var.athena_results_prefix}"
    }
  }
}