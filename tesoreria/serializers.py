from rest_framework import serializers
from .models import CuentaBancaria, Gasto, Pago

class CuentaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaBancaria
        fields = '__all__'

class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'