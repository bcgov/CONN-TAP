module "app_ecr" {
  source = "../../modules/ecr_repositories"

  name_prefix      = "${var.license}-${var.env}-app"
  repository_names = ["backend", "frontend"]

  image_tag_mutability = "MUTABLE"

  untagged_image_expire_after_days = 14
  tagged_image_expire_after_days   = 30

  tags = {
    Environment = var.env
    License     = var.license
    Application = "conn-tap"
  }
}
