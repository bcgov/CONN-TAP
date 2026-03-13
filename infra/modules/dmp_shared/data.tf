data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = [var.vpc_name]
  }
}

data "aws_subnet" "ec2_subnet" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  filter {
    name   = "tag:Name"
    values = [var.ec2_subnet_name]
  }
}

data "aws_security_groups" "ec2_sgs" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  filter {
    name   = "group-name"
    values = var.ec2_security_group_names
  }
}