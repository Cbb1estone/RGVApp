# ─── Subnet Group para RDS ────────────────────────────────────────────────────
resource "aws_db_subnet_group" "db_subnets" {
  name        = "db-subnet-group"
  description = "Subnets para la instancia RDS PostgreSQL"
  subnet_ids  = [aws_subnet.public_subnet_a.id, aws_subnet.public_subnet_b.id]
  tags        = { Name = "tesoreria-db-subnet-group" }
}

# ─── RDS PostgreSQL ───────────────────────────────────────────────────────────
resource "aws_db_instance" "postgres" {
  allocated_storage   = 20
  engine              = "postgres"
  engine_version      = "15.7"
  instance_class      = "db.t3.micro"
  db_name             = "tesoreria_db"
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true

  db_subnet_group_name   = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  publicly_accessible    = false

  tags = { Name = "tesoreria-postgres" }
}
