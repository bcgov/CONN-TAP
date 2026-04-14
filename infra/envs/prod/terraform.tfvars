# Will be set via environment variable
# aws_region = "ca-central-1"
# license = "dd5a29"
# env     = "prod"

# Defaults are set in variables.tf — uncomment below to override:
# ec2_security_group_names = ["App"]
# powerbi_instance_type    = "t3.large"
# assets_dir               = "../../.."
#
# EKS + Superset (required for apply), or set the same names via TF_VAR_* from a .env:
# superset_acm_certificate_arn = "arn:aws:acm:ca-central-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
# superset_ingress_host        = "superset.example.stratus.cloud.gov.bc.ca"
# superset_init_admin_password = "use-a-strong-password"
# superset_redis_password      = optional; omit to auto-generate in Terraform state
