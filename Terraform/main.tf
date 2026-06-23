terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" 
}

# (VPC)
resource "aws_vpc" "django_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "tesoreria-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.django_vpc.id
}

resource "aws_subnet" "public_subnet_a" {
  vpc_id            = aws_vpc.django_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "public_subnet_b" {
  vpc_id            = aws_vpc.django_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.django_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_subnet_a.id
  route_table_id = aws_route_table.public_rt.id
}

# 2. Grupos de Seguridad (Firewalls)
resource "aws_security_group" "ec2_sg" {
  name   = "Nvg-ec2-sg"
  vpc_id = aws_vpc.django_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
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
}

resource "aws_security_group" "db_sg" {
  name   = "django-db-sg"
  vpc_id = aws_vpc.django_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id] 
  }
}

# 3. Base de Datos en la nube (AWS RDS PostgreSQL)
resource "aws_db_subnet_group" "db_subnets" {
  name       = "db-subnet-group"
  subnet_ids = [aws_subnet.public_subnet_a.id, aws_subnet.public_subnet_b.id]
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = "db.t3.micro" # Entra en la capa gratuita
  db_name              = "tesoreria_db"
  username             = "db_admin"
  password             = "PasswordSeguro123" 
  skip_final_snapshot  = true
  db_subnet_group_name = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
}

# 4. Servidor Web (AWS EC2)
resource "aws_instance" "django_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS en us-east-1
  instance_type = "t2.micro"             # Entra en la capa gratuita

  subnet_id              = aws_subnet.public_subnet_a.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  tags = { Name = "Django-Tesoreria-Server" }

  # Script de automatización para instalar dependencias y clonar tu código
  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y python3-pip python3-dev libpq-dev git
              # Aquí clonarías tu repositorio de GitHub recién subido
              # git clone https://github.com/tu_usuario/RGVApp.git
              EOF
}

output "server_public_ip" {
  value       = aws_instance.django_server.public_ip
  description = "IP pública del servidor para acceder a tu app"
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}