data "aws_iam_policy_document" "pod_identity_trust" {
  statement {
    sid     = "EksPodIdentity"
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [var.cluster_arn]
    }
  }
}

resource "aws_iam_role" "alb_controller" {
  name                 = var.role_name
  assume_role_policy   = data.aws_iam_policy_document.pod_identity_trust.json
  permissions_boundary = null
  tags                 = var.tags
}

resource "aws_iam_policy" "alb_controller" {
  name_prefix = "${var.role_name}-policy-"
  policy      = file(var.policy_file_path)
  tags        = var.tags
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  role       = aws_iam_role.alb_controller.name
  policy_arn = aws_iam_policy.alb_controller.arn
}

# aws_eks_pod_identity_association is created in the environment root after
# kubernetes_service_account exists (AWS requirement).
