# PowerBI Desktop EC2 instance
resource "aws_instance" "powerbi_desktop_app_subnet" {
  ami                    = "ami-02bce8b27768e3fdf"
  instance_type          = "t3.large"
  subnet_id              = "subnet-0bace7fcb69dcfb23"
  vpc_security_group_ids = ["sg-0815d20af9a7d1a15", "sg-0803ebb9072902d62"]
  key_name               = "KP-EC2-redshift-powerbi"
  iam_instance_profile   = aws_iam_instance_profile.to_ec2_powerbi_athena_profile.name

  tags = {
    Name     = "ec2-50gb-powerbi-desktop-app-subnet"
    Critical = "Yes"
    Owner    = "Telecom Office Data Analytics / Engineering Team"
    Purpose  = "PowerBI Refresh / Publishing"
  }

  lifecycle {
    ignore_changes = [
      user_data,
      user_data_base64,
      associate_public_ip_address,
      private_ip,
      ipv6_addresses,
      credit_specification,
      monitoring,
      ebs_optimized,
      root_block_device,
      ebs_block_device,
      metadata_options,
      network_interface,
      disable_api_termination,
      instance_initiated_shutdown_behavior
    ]
  }
}