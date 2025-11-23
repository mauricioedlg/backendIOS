from decimal import Decimal
from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    correo = models.EmailField(max_length=100, unique=True)
    contrasena = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    clabe = models.CharField(max_length=30, blank=True, null=True)
    cuenta_bancaria = models.CharField(max_length=50, blank=True, null=True)
    saldo = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('1000.00'))
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuarios"
        managed = False  # cambia a True si Django debe controlar tablas

    def __str__(self):
        return f"{self.nombre or self.correo} ({self.id_usuario})"


class Accion(models.Model):
    id_accion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=18, decimal_places=2)
    cambio_porcentual = models.DecimalField(max_digits=7, decimal_places=2)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acciones"
        managed = False

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class Portafolio(models.Model):
    id_portafolio = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    accion = models.ForeignKey(Accion, on_delete=models.CASCADE, db_column="id_accion")
    cantidad = models.IntegerField()  # cuántas acciones posee el usuario
    precio_promedio = models.DecimalField(max_digits=18, decimal_places=4)  # precio promedio de compra
    fecha_ultima_operacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portafolio"
        managed = False
        unique_together = ('usuario', 'accion')

    def __str__(self):
        return f"{self.usuario} - {self.accion} x{self.cantidad}"


class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('DEPOSITO', 'Depósito'),
        ('RETIRO', 'Retiro'),
        ('COMPRA', 'Compra'),
        ('VENTA', 'Venta'),
    ]

    id_transaccion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    accion = models.ForeignKey(Accion, on_delete=models.SET_NULL, db_column="id_accion", null=True, blank=True)
    cantidad = models.IntegerField(null=True, blank=True)  # cantidad de acciones (si aplica)
    monto = models.DecimalField(max_digits=18, decimal_places=2)  # monto de la operación (pesos/moneda)
    saldo_anterior = models.DecimalField(max_digits=18, decimal_places=2)
    saldo_nuevo = models.DecimalField(max_digits=18, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transacciones"
        managed = False

    def __str__(self):
        return f"{self.tipo} - {self.usuario} - {self.monto}"


class ConfigMonto(models.Model):
    """
    Tabla para definir montos válidos de depósito/retiro que solo el backend/SQL puede editar.
    Por ejemplo: id=1 => depositar 100, id=2 => depositar 500, etc.
    """
    id_config = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20)  # DEPOSITO o RETIRO
    monto = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "config_montos"
        managed = False

    def __str__(self):
        return f"{self.tipo} - {self.monto}"
