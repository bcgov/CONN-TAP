# EKS, platform Postgres RDS, ECR, GitHub OIDC, and LZA internal ALB controller.
# DMP shared resources (S3, Glue, Athena, Lambdas, PowerBI EC2, etc.) remain under
# ../../modules/ for reference. The conn-tap app Helm release is deployed by GitHub Actions.

data "aws_caller_identity" "current" {}
