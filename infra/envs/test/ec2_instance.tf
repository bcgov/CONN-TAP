# Security group for RDP when ec2_rdp_allowed_cidr is set (port forwarding via SSM works without this)
resource "aws_security_group" "ec2_rdp" {
  count = var.enable_ec2 && var.ec2_rdp_allowed_cidr != "" ? 1 : 0

  name        = "${var.ec2_name}-rdp-${var.account_id}"
  description = "Allow RDP to PowerBI EC2 from specified CIDR"
  vpc_id      = var.vpc_id

  ingress {
    description = "RDP"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = [var.ec2_rdp_allowed_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.ec2_name}-rdp-${var.account_id}"
  }
}

# PowerBI Desktop EC2 instance for Athena/Glue queries
resource "aws_instance" "powerbi_desktop" {
  count = var.enable_ec2 ? 1 : 0

  ami           = var.powerbi_ami
  instance_type = var.ec2_instance_type
  key_name      = var.ec2_key_name
  subnet_id     = var.ec2_subnet_id
  vpc_security_group_ids = var.ec2_rdp_allowed_cidr != "" ? concat(var.ec2_security_group_ids, [aws_security_group.ec2_rdp[0].id]) : var.ec2_security_group_ids

  iam_instance_profile = aws_iam_instance_profile.to_ec2_powerbi_athena_profile.name

  # Enable Remote Desktop on first boot
  user_data = <<-EOF
    <powershell>
    Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
    </powershell>
  EOF

  root_block_device {
    volume_size = var.ec2_root_volume_gb
    volume_type = "gp3"
  }

  tags = {
    Name = "${var.ec2_name}-${var.account_id}"
  }

  depends_on = [
    aws_iam_role_policy_attachment.to_ec2_cloudwatch_agent,
    aws_iam_role_policy_attachment.to_ec2_ssm_ds,
    aws_iam_role_policy_attachment.to_ec2_ssm_core,
    aws_iam_role_policy_attachment.to_ec2_glue_full,
    aws_iam_role_policy_attachment.to_ec2_athena_full,
    aws_iam_role_policy_attachment.to_ec2_s3_full,
  ]
}
