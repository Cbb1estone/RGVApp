output "server_public_ip" {
  value       = aws_instance.django_server.public_ip
  description = "IP pública del servidor para acceder a tu app"
}

output "db_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Endpoint de conexión a la base de datos PostgreSQL"
  sensitive   = true
}
