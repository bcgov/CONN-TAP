# GitHub Actions OIDC trust for AWS, per BC Gov LZA guidance.
# Creates (optionally) the account-level OIDC provider and an IAM role that GitHub
# Actions can assume via sts:AssumeRoleWithWebIdentity. Restricts the trust to
# specific repositories and (optionally) specific subjects (branches/environments/tags).
#
# References:
#   https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
#   https://developer.gov.bc.ca/docs/default/component/public-cloud-techdocs/aws/LZA/best-practices/iac-and-ci-cd/

locals {
  oidc_url    = "token.actions.githubusercontent.com"
  oidc_issuer = "https://${local.oidc_url}"

  # Default subject pattern when none is supplied: allow any workflow in the listed repos.
  # Tighten in callers to specific branches/environments — see variable description.
  default_subjects   = [for r in var.github_repositories : "repo:${r}:*"]
  effective_subjects = length(var.allowed_subjects) > 0 ? var.allowed_subjects : local.default_subjects
}

# AWS publishes the GitHub OIDC thumbprint, but rotation is automatic since 2023.
# Fingerprint here is the documented one; AWS no longer enforces it strictly but
# the provider resource still requires the field.
resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = local.oidc_issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = var.oidc_thumbprints

  tags = var.tags
}

# Lookup the existing provider when create_oidc_provider = false.
data "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 0 : 1
  url   = local.oidc_issuer
}

locals {
  provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
}

data "aws_iam_policy_document" "trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_url}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.oidc_url}:sub"
      values   = local.effective_subjects
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name                 = var.role_name
  description          = "Assumed by GitHub Actions via OIDC for ${var.role_name}."
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = var.max_session_duration

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "managed" {
  for_each = toset(var.managed_policy_arns)

  role       = aws_iam_role.github_actions.name
  policy_arn = each.value
}

resource "aws_iam_role_policy" "inline" {
  count = var.inline_policy_json == null ? 0 : 1

  name   = "${var.role_name}-inline"
  role   = aws_iam_role.github_actions.id
  policy = var.inline_policy_json
}
