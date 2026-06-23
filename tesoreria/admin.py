from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import CuentaBancaria, Gasto, Pago

@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'banco', 'saldo_actual')


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'monto_total', 'monto_pendiente', 'estado')
    list_filter = ('estado',)
    # Acciones de la app
    actions = ['aprobar_gasto', 'cancelar_gasto', 'generar_pago_automatico']

    def aprobar_gasto(self, request, queryset):
        for gasto in queryset:
            if gasto.estado == 'PENDIENTE':
                gasto.estado = 'APROBADO'
                gasto.save()
                self.message_user(request, f"Gasto '{gasto.descripcion}' aprobado con éxito.")
            else:
                self.message_user(request, f"No se pudo aprobar '{gasto.descripcion}' (Solo se pueden aprobar pendientes).", messages.WARNING)
    aprobar_gasto.short_description = "Aprobar gastos seleccionados"

    def cancelar_gasto(self, request, queryset):
        for gasto in queryset:
            gasto.estado = 'CANCELADO'
            try:
                gasto.save()
                self.message_user(request, f"Gasto '{gasto.descripcion}' cancelado.")
            except ValidationError as e:
                self.message_user(request, str(e), messages.ERROR)
    cancelar_gasto.short_description = "Cancelar gastos seleccionados"

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('gasto', 'cuenta', 'monto', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    actions = ['efectuar_pago', 'cancelar_pago']

    def efectuar_pago(self, request, queryset):
        for pago in queryset:
            if pago.estado == 'PENDIENTE':
                pago.estado = 'EFECTUADO'
                try:
                    pago.save()
                    self.message_user(request, f"Pago por ${pago.monto} EFECTUADO con éxito. Se descontó del saldo.")
                except ValidationError as e:
                    pago.estado = 'PENDIENTE' # Revertir estado si falla la validación
                    self.message_user(request, str(e), messages.ERROR)
            else:
                self.message_user(request, "Este pago ya fue procesado o cancelado.", messages.WARNING)
    efectuar_pago.short_description = "Efectuar pagos seleccionados (Descuenta saldo)"

    def cancelar_pago(self, request, queryset):
        for pago in queryset:
            if pago.estado == 'PENDIENTE':
                pago.estado = 'CANCELADO'
                pago.save()
                self.message_user(request, f"Pago cancelado.")
            else:
                self.message_user(request, "Solo se pueden cancelar pagos en estado Pendiente.", messages.WARNING)
    cancelar_pago.short_description = "Cancelar pagos seleccionados"