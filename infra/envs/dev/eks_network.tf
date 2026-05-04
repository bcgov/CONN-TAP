locals {
  vpc_name = title(var.env)

  lza_subnet_name_app_a  = coalesce(var.lza_subnet_name_app_a, "${title(var.env)}-App-A")
  lza_subnet_name_app_b  = coalesce(var.lza_subnet_name_app_b, "${title(var.env)}-App-B")
  lza_subnet_name_data_a = coalesce(var.lza_subnet_name_data_a, "${title(var.env)}-Data-A")
  lza_subnet_name_data_b = coalesce(var.lza_subnet_name_data_b, "${title(var.env)}-Data-B")
  lza_subnet_name_management_a = coalesce(var.lza_subnet_name_management_a, "${title(var.env)}-Mgmt-A")
  lza_subnet_name_management_b = coalesce(var.lza_subnet_name_management_b, "${title(var.env)}-Mgmt-B")

  eks_cluster_name    = "${var.license}-${var.env}-eks"
  rds_resource_prefix = "${var.license}-${var.env}"
}

data "aws_vpc" "workload" {
  filter {
    name   = "tag:Name"
    values = [local.vpc_name]
  }
}

data "aws_subnet" "app_a" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_app_a]
  }
}

data "aws_subnet" "app_b" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_app_b]
  }
}

data "aws_subnet" "data_a" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_data_a]
  }
}

data "aws_subnet" "data_b" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_data_b]
  }
}

data "aws_subnet" "management_a" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_management_a]
  }
}

data "aws_subnet" "management_b" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.workload.id]
  }
  filter {
    name   = "tag:Name"
    values = [local.lza_subnet_name_management_b]
  }
}
