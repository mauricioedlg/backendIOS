# core/views.py
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from .models import Usuario, Accion, Portafolio, Transaccion
from .serializers import UsuarioSerializer, AccionSerializer, PortafolioSerializer, TransaccionSerializer

# ----- ViewSets existentes (CRUD genérico) -----
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class AccionViewSet(viewsets.ModelViewSet):
    queryset = Accion.objects.all()
    serializer_class = AccionSerializer

class PortafolioViewSet(viewsets.ModelViewSet):
    queryset = Portafolio.objects.all()
    serializer_class = PortafolioSerializer

class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer


# ----- Endpoints personalizados para la app Swift -----

@api_view(['POST'])
def login(request):
    correo = request.data.get("correo")
    contrasena = request.data.get("contrasena")
    if not correo or not contrasena:
        return Response({"error": "Faltan credenciales"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        usuario = Usuario.objects.get(correo=correo, contrasena=contrasena)
        data = UsuarioSerializer(usuario).data
        # No devolver la contraseña (por seguridad en API)
        data.pop('contrasena', None)
        return Response(data, status=status.HTTP_200_OK)
    except Usuario.DoesNotExist:
        return Response({"error": "Credenciales incorrectas"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def obtener_portafolio_usuario(request, id_usuario):
    port = Portafolio.objects.filter(usuario_id=id_usuario)
    data = PortafolioSerializer(port, many=True).data
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def comprar_accion(request):
    """
    Body: {
      "id_usuario": 1,
      "id_accion": 2,
      "monto": 1500.00
    }
    """
    id_usuario = request.data.get("id_usuario")
    id_accion = request.data.get("id_accion")
    monto = request.data.get("monto")

    if not id_usuario or not id_accion or monto is None:
        return Response({"error": "Parámetros incompletos"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    accion = get_object_or_404(Accion, pk=id_accion)

    # Verificar saldo
    if usuario.saldo < float(monto):
        return Response({"error": "Saldo insuficiente"}, status=status.HTTP_400_BAD_REQUEST)

    # Descontar saldo (nota: managed=False, hacemos update por queryset)
    Usuario.objects.filter(pk=usuario.id_usuario).update(saldo=usuario.saldo - float(monto))

    # Insertar/actualizar portafolio: si ya tiene la accion, sumamos monto; si no, creamos registro
    existing = Portafolio.objects.filter(usuario_id=id_usuario, accion_id=id_accion).first()
    if existing:
        new_monto = float(existing.monto_invertido) + float(monto)
        Portafolio.objects.filter(pk=existing.id_portafolio).update(monto_invertido=new_monto)
    else:
        Portafolio.objects.create(
            usuario_id=id_usuario,
            accion_id=id_accion,
            porcentaje=0,
            monto_invertido=monto
        )

    # Registrar transacción
    Transaccion.objects.create(
        usuario_id=id_usuario,
        descripcion=f"Compra acción {accion.nombre}",
        monto=monto
    )

    # Devolver portafolio actualizado
    port = Portafolio.objects.filter(usuario_id=id_usuario)
    return Response(PortafolioSerializer(port, many=True).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def vender_accion(request):
    """
    Body: {
      "id_usuario": 1,
      "id_accion": 2,
      "monto": 500.00
    }
    """
    id_usuario = request.data.get("id_usuario")
    id_accion = request.data.get("id_accion")
    monto = request.data.get("monto")

    if not id_usuario or not id_accion or monto is None:
        return Response({"error": "Parámetros incompletos"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    accion = get_object_or_404(Accion, pk=id_accion)

    existing = Portafolio.objects.filter(usuario_id=id_usuario, accion_id=id_accion).first()
    if not existing:
        return Response({"error": "No existe la acción en el portafolio"}, status=status.HTTP_400_BAD_REQUEST)

    if float(monto) >= float(existing.monto_invertido):
        # Vendió todo -> eliminar registro
        Portafolio.objects.filter(pk=existing.id_portafolio).delete()
    else:
        new_monto = float(existing.monto_invertido) - float(monto)
        Portafolio.objects.filter(pk=existing.id_portafolio).update(monto_invertido=new_monto)

    # Aumentar saldo del usuario
    Usuario.objects.filter(pk=usuario.id_usuario).update(saldo=usuario.saldo + float(monto))

    # Registrar transacción
    Transaccion.objects.create(
        usuario_id=id_usuario,
        descripcion=f"Venta acción {accion.nombre}",
        monto=float(monto) * -1
    )

    port = Portafolio.objects.filter(usuario_id=id_usuario)
    return Response(PortafolioSerializer(port, many=True).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def depositar_retiro(request):
    """
    Body: {
      "id_usuario": 1,
      "monto": 1000.00,
      "tipo": "depositar" | "retirar"
    }
    Nota: según tu requerimiento, el monto puede venir de SQL en vez de ser ingresado por frontend.
    """
    id_usuario = request.data.get("id_usuario")
    monto = request.data.get("monto")
    tipo = request.data.get("tipo")

    if not id_usuario or monto is None or tipo not in ("depositar", "retirar"):
        return Response({"error": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)

    if tipo == "retirar" and usuario.saldo < float(monto):
        return Response({"error": "Saldo insuficiente"}, status=status.HTTP_400_BAD_REQUEST)

    new_saldo = usuario.saldo + float(monto) if tipo == "depositar" else usuario.saldo - float(monto)
    Usuario.objects.filter(pk=usuario.id_usuario).update(saldo=new_saldo)

    Transaccion.objects.create(
        usuario_id=id_usuario,
        descripcion=f"{'Depósito' if tipo == 'depositar' else 'Retiro'} de ${monto}",
        monto=monto if tipo == "depositar" else float(monto) * -1
    )

    return Response({"saldo": new_saldo}, status=status.HTTP_200_OK)


@api_view(['PUT'])
def editar_usuario(request, id_usuario):
    """
    Body: {
      "nombre": "...",
      "direccion": "...",
      "clabe": "...",
      "cuenta_bancaria": "..."
    }
    """
    usuario = get_object_or_404(Usuario, pk=id_usuario)
    data = request.data

    # Actualizamos sólo campos permitidos
    update_fields = {}
    if "nombre" in data: update_fields["nombre"] = data["nombre"]
    if "direccion" in data: update_fields["direccion"] = data["direccion"]
    if "clabe" in data: update_fields["clabe"] = data["clabe"]
    if "cuenta_bancaria" in data: update_fields["cuenta_bancaria"] = data["cuenta_bancaria"]

    if update_fields:
        Usuario.objects.filter(pk=usuario.id_usuario).update(**update_fields)

    updated = Usuario.objects.get(pk=usuario.id_usuario)
    serialized = UsuarioSerializer(updated).data
    serialized.pop("contrasena", None)
    return Response(serialized, status=status.HTTP_200_OK)
