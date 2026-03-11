variable "aws_region" { type = string }
variable "account_id" { type = string }

variable "vpc_id" { type = string }
variable "ec2_subnet_id" { type = string }
variable "ec2_security_group_ids" { type = list(string) }

variable "glue_assets_bucket" { type = string }
variable "athena_results_prefix" { type = string }

variable "ngta_raw_bucket" { type = string }
variable "tsma_raw_bucket" { type = string }
variable "tsma_ngta_mapping_bucket" { type = string }
variable "tsma_ngta_price_books_bucket" { type = string }

variable "powerbi_ami" { type = string }
variable "powerbi_key_name" { type = string }

variable "ec2_instance_profile_name" { type = string }
variable "ec2_key_name" { type = string }
variable "ec2_public_key" { type = string }

variable "enable_redshift" { type = bool }
variable "redshift_cluster_identifier" { type = string }
variable "redshift_node_type" { type = string }
variable "redshift_master_username" { type = string }
variable "redshift_database_name" { type = string }
variable "redshift_subnet_ids" { type = list(string) }
variable "redshift_security_group_id" { type = string }

variable "enable_tsma_lambda_fact" { type = bool }