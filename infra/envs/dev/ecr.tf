module "app_ecr" {
  source = "../../modules/ecr_repositories"

  name_prefix      = "${var.license}-${var.env}-app"
  repository_names = ["backend", "frontend"]

  image_tag_mutability = "MUTABLE"

  tags = {
    Environment = var.env
    License     = var.license
    Application = "conn-tap"
  }
}
