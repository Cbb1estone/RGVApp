terraform {
  required_version = ">= 0.12"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = var.access_key
  secret_key = var.secret_key
}

# ─── EC2: Servidor Django ─────────────────────────────────────────────────────
resource "aws_instance" "django_server" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t3.micro"
  key_name      = "rgvapp-key"

  subnet_id              = aws_subnet.public_subnet_a.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  tags = { Name = "Django-Tesoreria-Server" }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    exec > /var/log/user-data.log 2>&1

    # ── 1. Dependencias del sistema ──────────────────────────────────────────
    apt-get update -y
    apt-get install -y python3-pip python3-dev libpq-dev git nginx

    # ── 2. Clonar el proyecto ────────────────────────────────────────────────
    cd /home/ubuntu
    git clone https://github.com/Cbb1estone/RGVApp.git
    cd RGVApp

    # ── 3. Instalar dependencias Python ─────────────────────────────────────
    pip3 install -r requirements.txt
    pip3 install gunicorn psycopg2-binary

    # ── 4. Variables de entorno ──────────────────────────────────────────────
    cat > /home/ubuntu/RGVApp/.env <<ENVFILE
    SECRET_KEY=${var.django_secret_key}
    DEBUG=False
    ALLOWED_HOSTS=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4),localhost
    DATABASE_URL=postgres://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/tesoreria_db
    ENVFILE

    # ── 5. Migraciones y archivos estáticos ─────────────────────────────────
    cd /home/ubuntu/RGVApp
    python3 manage.py migrate --noinput
    python3 manage.py collectstatic --noinput

    # ── 6. Servicio systemd para Gunicorn ────────────────────────────────────
    cat > /etc/systemd/system/gunicorn.service <<SERVICE
    [Unit]
    Description=Gunicorn daemon para Django Tesoreria
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu/RGVApp
    EnvironmentFile=/home/ubuntu/RGVApp/.env
    ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 RGVApp.wsgi:application

    [Install]
    WantedBy=multi-user.target
    SERVICE

    systemctl daemon-reload
    systemctl enable gunicorn
    systemctl start gunicorn

    # ── 7. Nginx como proxy inverso ──────────────────────────────────────────
    cat > /etc/nginx/sites-available/rgvapp <<NGINX
    server {
        listen 80;
        server_name _;

        location /static/ {
            alias /home/ubuntu/RGVApp/staticfiles/;
        }

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
        }
    }
    NGINX

    ln -sf /etc/nginx/sites-available/rgvapp /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    systemctl restart nginx
    systemctl enable nginx

    echo "✅ Despliegue completo"
  EOF

  # Esperar a que la DB esté lista antes de que EC2 corra el user_data
  depends_on = [aws_db_instance.postgres]
}
