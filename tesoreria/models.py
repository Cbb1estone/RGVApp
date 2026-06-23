import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class CuentaBancaria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la cuenta")
    banco = models.CharField(max_length=100)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nombre} ({self.banco}) - Saldo: ${self.saldo_actual}"


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
    monto_pendiente = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"{self.descripcion} - Total: ${self.monto_total} ({self.estado})"

    def save(self, *args, **kwargs):
        # Si es un gasto nuevo, el monto pendiente es igual al total
        if not self.pk:
            self.monto_pendiente = self.monto_total
        else:
            # REGLA: Gastos cancelados no se pueden volver a activar o modificar
            original = Gasto.objects.get(pk=self.pk)
            if original.estado == 'CANCELADO' and self.estado != 'CANCELADO':
                raise ValidationError("REGLA DE NEGOCIO: Un gasto cancelado no puede ser reactivado.")
        
        super().save(*args, **kwargs)


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
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Token único para evitar cobros dobles por error de clic repetido
    token_duplicado = models.CharField(max_length=100, unique=True, editable=False, blank=True)

    def __str__(self):
        return f"Pago de ${self.monto} para {self.gasto.descripcion} ({self.estado})"

    def clean(self):
        # REGLA: El Gasto debe estar aprobado antes de generar o efectuar un pago
        if self.gasto.estado not in ['APROBADO', 'PAGADO_PARCIAL']:
            raise ValidationError("REGLA DE NEGOCIO: El gasto debe estar APROBADO antes de poder registrar un pago.")

        # REGLA: Un pago parcial o total no puede exceder el monto pendiente del gasto
        if self.monto > self.gasto.monto_pendiente and self.estado != 'CANCELADO':
            raise ValidationError(f"REGLA DE NEGOCIO: El monto del pago (${self.monto}) excede el saldo pendiente del gasto (${self.gasto.monto_pendiente}).")

        # REGLA: El pago no puede exceder el saldo disponible de la cuenta bancaria (Solo si se va a efectuar)
        if self.estado == 'EFECTUADO' and self.monto > self.cuenta.saldo_actual:
            raise ValidationError(f"REGLA DE NEGOCIO: Saldo insuficiente en la cuenta. Disponible: ${self.cuenta.saldo_actual}")

    def save(self, *args, **kwargs):
        # Ejecuta las validaciones de la función clean() antes de guardar
        self.full_clean()

        # REGLA: Evitar pagos duplicados utilizando una huella digital única (mismo gasto, cuenta y monto en corto tiempo)
        if not self.token_duplicado:
            self.token_duplicado = f"{self.gasto_id}-{self.cuenta_id}-{self.monto}-{timezone.now().strftime('%Y%m%d%H%M')}"

        # Lógica si el pago se marca como EFECTUADO
        if self.estado == 'EFECTUADO':
            # 1. Restar saldo de la cuenta bancaria
            self.cuenta.saldo_actual -= self.monto
            self.cuenta.save()

            # 2. Actualizar el gasto asociado
            self.gasto.monto_pendiente -= self.monto
            if self.gasto.monto_pendiente == 0:
                self.gasto.estado = 'PAGADO_TOTAL'
            else:
                self.gasto.estado = 'PAGADO_PARCIAL'
            self.gasto.save()

        super().save(*args, **kwargs)