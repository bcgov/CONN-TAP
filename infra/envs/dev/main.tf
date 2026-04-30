# Only EKS and the Postgres RDS are deployed from this environment.
# DMP shared resources (S3 buckets, Glue, Athena, Lambdas, PowerBI EC2, etc.)
# and Superset (Helm release, namespace, ALB controller, bastion) are intentionally
# disabled here. The corresponding modules remain under ../../modules/ for reference.

data "aws_caller_identity" "current" {}
