# PowerBI Desktop EC2 instance for Athena/Glue queries
resource "aws_instance" "powerbi_desktop" {
  count = var.enable_ec2 ? 1 : 0

  ami                    = var.powerbi_ami
  instance_type          = var.ec2_instance_type
  key_name               = var.powerbi_key_name
  subnet_id              = var.ec2_subnet_id
  vpc_security_group_ids = var.ec2_security_group_ids

  iam_instance_profile = aws_iam_instance_profile.to_ec2_powerbi_athena_profile.name

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
