from django.db import models
from django.contrib.auth.models import User

class CuentaBancaria(models.Model):
    nombre = models.CharField(max_length=100)
    banco = models.CharField(max_length=100)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2)

class Gasto(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('CANCELADO', 'Cancelado'),
        ('PAGADO_PARCIAL', 'Pagado Parcial'),
        ('PAGADO_TOTAL', 'Pagado Total'),
    )
    descripcion = models.CharField(max_length=255)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    monto_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

class Pago(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente de Efectuar'),
        ('EFECTUADO', 'Efectuado'),
        ('CANCELADO', 'Cancelado'),
    )
    gasto = models.ForeignKey(Gasto, on_delete=models.CASCADE, related_name='pagos')
    cuenta = models.ForeignKey(CuentaBancaria, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    # Para evitar pagos duplicados (Regla de negocio) 
    uuid_transaccion = models.UUIDField(unique=True, editable=False)