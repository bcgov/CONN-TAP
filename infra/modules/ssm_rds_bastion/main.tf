data "aws_vpc" "this" {
  id = var.vpc_id
}

resource "aws_security_group" "bastion" {
  name_prefix = "${var.name_prefix}-ssm-bastion-"
  description = "SSM-only host for port-forwarding to RDS (no inbound traffic)."
  vpc_id      = var.vpc_id

  # No ingress — use Session Manager only.

  egress {
    description = "Egress for SSM, package updates, and PostgreSQL to RDS in VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-ssm-bastion" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_iam_role" "bastion" {
  name_prefix = "${var.name_prefix}-ssm-bastion-"
  description = "EC2 role for SSM Session Manager (${var.name_prefix})."

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.bastion.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion" {
  name_prefix = "${var.name_prefix}-ssm-bastion-"
  role        = aws_iam_role.bastion.name
}

resource "aws_instance" "bastion" {
  ami                    = "ami-0dd6ad74006372963"
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.bastion.id]

  iam_instance_profile = aws_iam_instance_profile.bastion.name

  monitoring = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-ssm-bastion" })
}
