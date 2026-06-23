from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from decimal import Decimal
import json

# Importaciones de los Modelos
from .models import CuentaBancaria, Gasto, Pago

# Importaciones para Django REST Framework
from rest_framework import viewsets
from .serializers import CuentaBancariaSerializer, GastoSerializer, PagoSerializer

class CuentaBancariaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CuentaBancaria.objects.all()
    serializer_class = CuentaBancariaSerializer

class GastoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer

class PagoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer

@login_required
def dashboard(request):
    cuentas = CuentaBancaria.objects.all()
    
    # Paginación de Gastos (Límite: 5 por página)
    gastos_list = Gasto.objects.all().order_by('-id')
    paginator_gastos = Paginator(gastos_list, 5)
    page_gastos = request.GET.get('page_gastos', 1)
    gastos = paginator_gastos.get_page(page_gastos)

    # Paginación de Pagos (Límite: 5 por página)
    pagos_list = Pago.objects.all().order_by('-id')
    paginator_pagos = Paginator(pagos_list, 5)
    page_pagos = request.GET.get('page_pagos', 1)
    pagos = paginator_pagos.get_page(page_pagos)

    nombres_cuentas = [c.nombre for c in cuentas]
    saldos_cuentas = [float(c.saldo_actual) for c in cuentas]

    context = {
        'cuentas': cuentas,
        'gastos': gastos,
        'pagos': pagos,
        'nombres_cuentas_json': json.dumps(nombres_cuentas),
        'saldos_cuentas_json': json.dumps(saldos_cuentas),
        'current_page_gastos': page_gastos,
        'current_page_pagos': page_pagos,
    }
    return render(request, 'tesoreria/dashboard.html', context)

@login_required
def crear_cuenta(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        banco = request.POST.get('banco')
        saldo = request.POST.get('saldo_actual')
        CuentaBancaria.objects.create(nombre=nombre, banco=banco, saldo_actual=saldo)
        messages.success(request, "Cuenta bancaria registrada con éxito.")
        return redirect('dashboard')
    return render(request, 'tesoreria/crear_cuenta.html')

@login_required
def crear_gasto(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        monto = request.POST.get('monto_total')
        Gasto.objects.create(descripcion=descripcion, monto_total=monto)
        messages.success(request, "Gasto registrado en estado Pendiente.")
        return redirect('dashboard')
    return render(request, 'tesoreria/crear_gasto.html')

# NUEVA VISTA: Agregar fondos/recursos a una cuenta
@login_required
def ingresar_recursos(request):
    cuentas = CuentaBancaria.objects.all()
    if request.method == 'POST':
        cuenta_id = request.POST.get('cuenta')
        
        # CORRECCIÓN: Convertimos a Decimal en lugar de float
        try:
            monto_ingreso = Decimal(request.POST.get('monto', '0'))
        except (ValueError, TypeError):
            monto_ingreso = Decimal('0')
        
        if monto_ingreso <= 0:
            messages.error(request, "El monto a ingresar debe ser mayor a 0.")
            return redirect('ingresar_recursos')
            
        cuenta = get_object_or_404(CuentaBancaria, id=cuenta_id)
        cuenta.saldo_actual += monto_ingreso  # ¡Ahora sí son del mismo tipo!
        cuenta.save()
        
        messages.success(request, f"¡Depósito exitoso! Se han agregado ${monto_ingreso} a la cuenta '{cuenta.nombre}'.")
        return redirect('dashboard')
        
    return render(request, 'tesoreria/ingresar_recursos.html', {'cuentas': cuentas})
@login_required
def solicitar_pago(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    cuentas = CuentaBancaria.objects.all()
    if request.method == 'POST':
        cuenta_id = request.POST.get('cuenta')
        cuenta = get_object_or_404(CuentaBancaria, id=cuenta_id)
        try:
            Pago.objects.create(gasto=gasto, cuenta=cuenta, monto=gasto.monto_pendiente, estado='PENDIENTE')
            messages.success(request, f"Pago pendiente ligado a la cuenta '{cuenta.nombre}' para '{gasto.descripcion}'.")
            return redirect('dashboard')
        except ValidationError as e:
            # CORRECCIÓN: Extrae el mensaje limpio si viene en un diccionario o lista
            error_msg = e.message_dict.get('__all__', [str(e)])[0] if hasattr(e, 'message_dict') else (e.messages[0] if hasattr(e, 'messages') else str(e))
            messages.error(request, error_msg)
            return redirect('dashboard')
    return render(request, 'tesoreria/solicitar_pago.html', {'gasto': gasto, 'cuentas': cuentas})

@login_required
def procesar_gasto(request, gasto_id, accion):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if accion == 'aprobar' and gasto.estado == 'PENDIENTE':
        gasto.estado = 'APROBADO'
        gasto.save()
        messages.success(request, f"Gasto '{gasto.descripcion}' aprobado con éxito.")
    elif accion == 'cancelar':
        gasto.estado = 'CANCELADO'
        gasto.save()
        messages.warning(request, f"Gasto '{gasto.descripcion}' cancelado.")
    return redirect('dashboard')

@login_required
def procesar_pago(request, pago_id, accion):
    pago = get_object_or_404(Pago, id=pago_id)
    try:
        if accion == 'efectuar' and pago.estado == 'PENDIENTE':
            pago.estado = 'EFECTUADO'
            pago.save()
            messages.success(request, f"Pago de ${pago.monto} efectuado. Saldo bancario descontado de {pago.cuenta.nombre}.")
        elif accion == 'cancelar' and pago.estado == 'PENDIENTE':
            pago.estado = 'CANCELADO'
            pago.save()
            messages.warning(request, "Pago cancelado de forma segura.")
    except ValidationError as e:
        # CORRECCIÓN: Extrae el mensaje limpio si viene en un diccionario o lista
        error_msg = e.message_dict.get('__all__', [str(e)])[0] if hasattr(e, 'message_dict') else (e.messages[0] if hasattr(e, 'messages') else str(e))
        messages.error(request, error_msg)
    return redirect('dashboard')

@login_required
def editar_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(CuentaBancaria, id=cuenta_id)
    if request.method == 'POST':
        cuenta.nombre = request.POST.get('nombre')
        cuenta.banco = request.POST.get('banco')
        cuenta.saldo_actual = Decimal(request.POST.get('saldo_actual', '0'))
        cuenta.save()
        messages.success(request, f"Cuenta '{cuenta.nombre}' actualizada con éxito.")
        return redirect('dashboard')
    return render(request, 'tesoreria/editar_cuenta.html', {'cuenta': cuenta})

@login_required
def eliminar_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(CuentaBancaria, id=cuenta_id)
    nombre_cuenta = cuenta.nombre
    
    # Validación opcional: Evitar eliminar si tiene pagos asociados
    if cuenta.pago_set.exists():
        messages.error(request, f"No se puede eliminar '{nombre_cuenta}' porque tiene un historial de pagos ligado.")
        return redirect('dashboard')
        
    cuenta.delete()
    messages.warning(request, f"La cuenta '{nombre_cuenta}' ha sido eliminada.")
    return redirect('dashboard')