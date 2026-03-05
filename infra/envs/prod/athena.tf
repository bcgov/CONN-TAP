resource "aws_athena_workgroup" "ngta_powerbi" {
  name        = "ngta_powerbi"
  description = "Athena DB for NGTA Telus and Rogers file to read Parquet"

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = 1099511627776000
    requester_pays_enabled             = false

    result_configuration {
      output_location = "s3://ngta-raw-data/athena_results/"
    }
  }
}