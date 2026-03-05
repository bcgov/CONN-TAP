terraform {
  backend "s3" {
    bucket = "terraform-remote-state-c4e70c-prod"
    key    = "ngta/terraform.tfstate"
    region = "ca-central-1"
  }
}