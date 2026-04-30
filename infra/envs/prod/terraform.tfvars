# Will be set via environment variable
# aws_region = "ca-central-1"   # only ca-central-1 is permitted for this account
# license    = "dd5a29"
# env        = "prod"

# Prod EKS sizing: 3 nodes (one per AZ), surge headroom up to 6 for rolling upgrades.
eks_node_instance_types = ["m5.large"]
eks_node_min_size       = 3
eks_node_desired_size   = 3
eks_node_max_size       = 6
