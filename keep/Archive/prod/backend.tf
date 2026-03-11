terraform {
  backend "s3" {
    bucket  = "terraform-remote-state-dd5a29-prod"
    key     = "dmp/terraform.tfstate"
    region  = "ca-central-1"
    encrypt = true
  }
}