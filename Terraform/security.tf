# ─── Security Group: EC2 ──────────────────────────────────────────────────────
resource "aws_security_group" "ec2_sg" {
  name        = "Nvg-ec2-sg"
  description = "Permite trafico HTTP, HTTPS y SSH al servidor Django"
  vpc_id      = aws_vpc.django_vpc.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FIX: agregar HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "Nvg-ec2-sg" }
}

# ─── Security Group: RDS ──────────────────────────────────────────────────────
resource "aws_security_group" "db_sg" {
  name        = "django-db-sg"
  description = "Permite acceso PostgreSQL solo desde el EC2"
  vpc_id      = aws_vpc.django_vpc.id

  ingress {
    description     = "PostgreSQL desde EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  # FIX: faltaba egress en el SG de la DB
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "django-db-sg" }
}
