resource "aws_key_pair" "powerbi" {
  key_name   = var.ec2_key_name
  public_key = var.ec2_public_key
}

resource "aws_instance" "powerbi_desktop" {
  ami                    = var.powerbi_ami
  instance_type          = var.ec2_instance_type
  key_name               = aws_key_pair.powerbi.key_name
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
    aws_key_pair.powerbi,
    aws_iam_instance_profile.to_ec2_powerbi_athena_profile
  ]
}