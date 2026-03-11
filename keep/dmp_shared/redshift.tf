resource "aws_redshift_subnet_group" "dmp" {
  count      = var.enable_redshift ? 1 : 0
  name       = "dmp-redshift-subnet-group"
  subnet_ids = var.redshift_subnet_ids

  tags = {
    Name = "dmp-redshift-subnet-group"
  }
}

resource "aws_redshift_cluster" "bc_redshift_cluster" {
  count                  = var.enable_redshift ? 1 : 0
  cluster_identifier     = var.redshift_cluster_identifier
  node_type              = var.redshift_node_type
  cluster_type           = "single-node"
  database_name          = var.redshift_database_name
  master_username        = var.redshift_master_username
  manage_master_password = true

  encrypted           = true
  publicly_accessible = false
  skip_final_snapshot = true

  cluster_subnet_group_name = aws_redshift_subnet_group.dmp[0].name
  vpc_security_group_ids    = [var.redshift_security_group_id]

  lifecycle {
    prevent_destroy = true
  }
}