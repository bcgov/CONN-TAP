terraform {
  backend "s3" {
    # bucket is supplied at init time to avoid hardcoding the license plate:
    # terraform init -backend-config=backend.hcl
    # where backend.hcl contains: bucket = "terraform-remote-state-<license>-prod"
    key     = "dmp/terraform.tfstate"
    region  = "ca-central-1"
    encrypt = true
  }
}
