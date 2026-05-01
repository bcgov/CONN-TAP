resource "aws_db_subnet_group" "superset" {
  name       = "${var.name_prefix}-db"
  subnet_ids = var.data_subnet_ids

  tags = merge(var.tags, { Name = "${var.name_prefix}-db" })
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.name_prefix}-pg-"
  description = "Platform metadata PostgreSQL (ingress via separate aws_vpc_security_group_ingress_rule resources)."
  vpc_id      = var.vpc_id

  # Do not define inline ingress: allowed_security_group_ids often include values
  # only known after apply (EKS, bastion), which causes "inconsistent final plan"
  # when using dynamic ingress blocks on this resource.

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-rds" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "postgres" {
  # Keys must be static (map keys); values may be unknown until apply — valid for for_each.
  for_each = var.allowed_security_group_ids

  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = each.value
  description                  = "PostgreSQL 5432 from ${each.key}"
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "random_password" "master" {
  length  = 24
  special = false
}

resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.name_prefix}/rds-master"
  recovery_window_in_days = 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = random_password.master.result
}

resource "aws_db_instance" "superset" {
  identifier     = var.name_prefix
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2
  storage_type          = "gp3"

  db_name  = var.db_name
  username = var.username
  password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.superset.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  storage_encrypted = true
  kms_key_id        = var.storage_kms_key_id

  backup_retention_period = var.backup_retention_period
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = var.deletion_protection
  multi_az                = var.multi_az

  tags = merge(var.tags, { Name = var.name_prefix })
}

# Async read replicas (no replicate_source_db ⇒ this is a primary; presence here ⇒ replica).
# Replicas live in the same subnet group / SG as the primary.
resource "aws_db_instance" "replica" {
  count = var.read_replica_count

  identifier             = "${var.name_prefix}-replica-${count.index + 1}"
  replicate_source_db    = aws_db_instance.superset.identifier
  instance_class         = coalesce(var.replica_instance_class, var.instance_class)
  vpc_security_group_ids = [aws_security_group.rds.id]

  storage_encrypted = true
  kms_key_id        = var.storage_kms_key_id

  skip_final_snapshot = true
  deletion_protection = var.deletion_protection

  tags = merge(var.tags, { Name = "${var.name_prefix}-replica-${count.index + 1}" })
}
