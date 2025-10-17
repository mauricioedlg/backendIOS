from django.db import models

# Create your models here.


from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    correo = models.EmailField(max_length=100, unique=True)
    contrasena = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuarios"   # 👈 aquí le dices que use tu tabla original
        managed = False



class Accion(models.Model):
    id_accion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=18, decimal_places=2)
    cambio_porcentual = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acciones"
        managed = False



class Portafolio(models.Model):
    id_portafolio = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    accion = models.ForeignKey(Accion, on_delete=models.CASCADE, db_column="id_accion")
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    monto_invertido = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "portafolio"
        managed = False



class Transaccion(models.Model):
    id_transaccion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transacciones"
        managed = False
