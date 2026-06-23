from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CuentaBancariaViewSet, 
    GastoViewSet, 
    PagoViewSet, 
    dashboard, 
    crear_cuenta, 
    crear_gasto, 
    ingresar_recursos, 
    solicitar_pago, 
    procesar_gasto, 
    procesar_pago,
    editar_cuenta,     
    eliminar_cuenta    
)

# Configuración del Router para la API de Django REST Framework
router = DefaultRouter()
router.register(r'cuentas', CuentaBancariaViewSet, basename='cuenta')
router.register(r'gastos', GastoViewSet, basename='gasto')
router.register(r'pagos', PagoViewSet, basename='pago')

urlpatterns = [
    # Rutas de la API
    path('api/', include(router.urls)),
    
    # Vista Principal / Dashboard
    path('', dashboard, name='dashboard'),
    
    # Rutas de Cuentas Bancarias
    path('cuenta/nueva/', crear_cuenta, name='crear_cuenta'),
    path('cuenta/ingresar/', ingresar_recursos, name='ingresar_recursos'),
    path('cuenta/<int:cuenta_id>/editar/', editar_cuenta, name='editar_cuenta'),
    path('cuenta/<int:cuenta_id>/eliminar/', eliminar_cuenta, name='eliminar_cuenta'),
    
    # Rutas de Gastos
    path('gasto/nuevo/', crear_gasto, name='crear_gasto'),
    path('gasto/<int:gasto_id>/preparar-pago/', solicitar_pago, name='solicitar_pago'),
    path('gasto/<int:gasto_id>/<str:accion>/', procesar_gasto, name='procesar_gasto'),
    
    # Rutas de Pagos
    path('pago/<int:pago_id>/<str:accion>/', procesar_pago, name='procesar_pago'),
]