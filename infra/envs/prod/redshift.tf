resource "aws_redshift_cluster" "bc_redshift_cluster" {
  cluster_identifier = "bc-redshift-cluster"
  node_type          = "dc2.large"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }
}