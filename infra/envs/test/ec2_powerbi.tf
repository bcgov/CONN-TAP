resource "aws_instance" "powerbi_desktop" {
  ami                    = var.powerbi_ami
  instance_type          = "t3.large"
  key_name               = var.powerbi_key_name
  subnet_id              = var.ec2_subnet_id
  vpc_security_group_ids = var.ec2_security_group_ids

  iam_instance_profile = aws_iam_instance_profile.to_ec2_powerbi_athena_profile.name

  tags = {
    Name = "ec2-powerbi-desktop-${var.account_id}"
  }
}
