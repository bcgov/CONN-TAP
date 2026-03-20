resource "aws_key_pair" "powerbi" {
  key_name   = var.powerbi_key_name
  public_key = var.ec2_public_key

  lifecycle {
    ignore_changes = [public_key]
  }
}

resource "aws_instance" "powerbi_desktop" {
  ami                         = var.powerbi_ami_id
  instance_type               = var.powerbi_instance_type
  subnet_id                   = data.aws_subnet.ec2_subnet.id
  vpc_security_group_ids      = data.aws_security_groups.ec2_sgs.ids
  iam_instance_profile        = aws_iam_instance_profile.to_ec2_powerbi_athena_profile.name
  key_name                    = aws_key_pair.powerbi.key_name
  associate_public_ip_address = false

  root_block_device {
    volume_size = 60
  }

  tags = {
    Name = var.powerbi_instance_name
  }
}