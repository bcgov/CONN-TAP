module "app_ecr" {
  source = "../../modules/ecr_repositories"

  name_prefix      = "${var.license}-${var.env}-app"
  repository_names = ["backend", "frontend"]

  tags = {
    Environment = var.env
    License     = var.license
    Application = "conn-tap"
  }
}
