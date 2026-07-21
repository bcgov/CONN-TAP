module "app_ecr" {
  source = "../../modules/ecr_repositories"

  name_prefix      = "${var.license}-${var.env}-app"
  repository_names = ["backend", "frontend"]

  untagged_image_expire_after_days = 90
  tagged_image_expire_after_days   = 90

  tags = {
    Environment = var.env
    License     = var.license
    Application = "conn-tap"
  }
}
