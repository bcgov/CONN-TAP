resource "aws_iam_role" "glue_role" {
  name        = "GlueS3RedshiftRole"
  description = "For BC DMP.Allows Glue to call AWS services on your behalf. "

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "glue.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "lambda_ngta_shared_role" {
  # shared by lambda-ngta-rogers and lambda-ngta-telus
  name = "lambda-ngta-telus-role-rachtis4"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "lambda_ngta_telus_quantities_role" {
  name = "lambda-ngta-telus-quantities-role-t2liebof"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}