resource "aws_ecr_repository" "this" {
  for_each = var.repository_names

  name                 = "${var.name_prefix}-${each.value}"
  image_tag_mutability = var.image_tag_mutability

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-${each.value}" })
}

locals {
  tagged_image_lifecycle_rule = var.tagged_image_expire_after_days == null ? [] : [
    {
      rulePriority = 2
      description  = "Delete tagged images older than ${var.tagged_image_expire_after_days} days"
      selection = {
        tagStatus   = "any"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = var.tagged_image_expire_after_days
      }
      action = {
        type = "expire"
      }
    }
  ]

  ecr_lifecycle_rules = concat(
    [
      {
        rulePriority = 1
        description  = "Delete untagged images older than ${var.untagged_image_expire_after_days} days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_expire_after_days
        }
        action = {
          type = "expire"
        }
      }
    ],
    local.tagged_image_lifecycle_rule,
  )
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name

  policy = jsonencode({
    rules = local.ecr_lifecycle_rules
  })
}
