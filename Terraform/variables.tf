# ─── Credenciales AWS ─────────────────────────────────────────────────────────
variable "access_key" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

# ─── Base de Datos ────────────────────────────────────────────────────────────
variable "db_username" {
  description = "Usuario administrador de la base de datos"
  type        = string
  default     = "db_admin"
}

variable "db_password" {
  description = "Contraseña del usuario administrador de la base de datos"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django SECRET_KEY para la configuración de la aplicación"
  type        = string
  sensitive   = true
}
