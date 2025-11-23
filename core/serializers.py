from rest_framework import serializers
from .models import Usuario, Accion, Portafolio, Transaccion, ConfigMonto

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'correo', 'nombre', 'direccion', 'clabe', 'cuenta_bancaria', 'saldo', 'fecha_registro']


class AccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accion
        fields = ['id_accion', 'nombre', 'precio', 'cambio_porcentual', 'fecha_actualizacion']


class PortafolioSerializer(serializers.ModelSerializer):
    accion = AccionSerializer(read_only=True)
    id_accion = serializers.PrimaryKeyRelatedField(queryset=Accion.objects.all(), source='accion', write_only=True)

    class Meta:
        model = Portafolio
        fields = ['id_portafolio', 'usuario', 'accion', 'id_accion', 'cantidad', 'precio_promedio', 'fecha_ultima_operacion']


class TransaccionSerializer(serializers.ModelSerializer):
    accion = AccionSerializer(read_only=True)
    class Meta:
        model = Transaccion
        fields = ['id_transaccion', 'usuario', 'tipo', 'accion', 'cantidad', 'monto', 'saldo_anterior', 'saldo_nuevo', 'descripcion', 'fecha']


class ConfigMontoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigMonto
        fields = ['id_config', 'tipo', 'monto']
