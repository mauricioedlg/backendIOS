from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Usuario, Accion, Portafolio, Transaccion, ConfigMonto
from .serializers import (UsuarioSerializer, AccionSerializer,
                          PortafolioSerializer, TransaccionSerializer, ConfigMontoSerializer)


# ViewSets CRUD básicos
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]


class AccionViewSet(viewsets.ModelViewSet):
    queryset = Accion.objects.all()
    serializer_class = AccionSerializer
    permission_classes = [AllowAny]


class PortafolioViewSet(viewsets.ModelViewSet):
    queryset = Portafolio.objects.select_related('accion', 'usuario').all()
    serializer_class = PortafolioSerializer
    permission_classes = [AllowAny]


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.select_related('accion', 'usuario').all().order_by('-fecha')
    serializer_class = TransaccionSerializer
    permission_classes = [AllowAny]


class ConfigMontoViewSet(viewsets.ModelViewSet):
    queryset = ConfigMonto.objects.all()
    serializer_class = ConfigMontoSerializer
    permission_classes = [AllowAny]


# ===============================
# Endpoints de negocio: comprar, vender, depositar, retirar
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def comprar(request):
    """
    POST /api/comprar/
    body: { "id_usuario": 1, "id_accion": 2, "cantidad": 10 }
    """
    data = request.data
    try:
        id_usuario = int(data.get('id_usuario'))
        id_accion = int(data.get('id_accion'))
        cantidad = int(data.get('cantidad'))
    except Exception:
        return Response({"detail": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

    if cantidad <= 0:
        return Response({"detail": "La cantidad debe ser mayor a 0"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    accion = get_object_or_404(Accion, pk=id_accion)

    monto_total = (Decimal(cantidad) * accion.precio).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    with transaction.atomic():
        # Refrescar saldo desde DB
        usuario = Usuario.objects.select_for_update().get(pk=usuario.id_usuario)
        saldo_anterior = usuario.saldo

        if saldo_anterior < monto_total:
            return Response({"detail": "Saldo insuficiente", "saldo_actual": f"{saldo_anterior}"}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar/crear portafolio
        portafolio, created = Portafolio.objects.select_for_update().get_or_create(
            usuario=usuario,
            accion=accion,
            defaults={'cantidad': cantidad, 'precio_promedio': accion.precio}
        )

        if not created:
            # calcular nuevo precio promedio ponderado
            total_acciones_previas = portafolio.cantidad
            precio_prom_prev = portafolio.precio_promedio
            nuevo_total_acciones = total_acciones_previas + cantidad
            # nuevo promedio = (previas*promedio + cantidad*precio_actual) / nuevo_total
            nuevo_promedio = ((Decimal(total_acciones_previas) * precio_prom_prev) + (Decimal(cantidad) * accion.precio)) / Decimal(nuevo_total_acciones)
            portafolio.cantidad = nuevo_total_acciones
            portafolio.precio_promedio = nuevo_promedio.quantize(Decimal('0.0001'), rounding=ROUND_DOWN)
            portafolio.save()
        else:
            portafolio.save()

        # Actualizar saldo usuario
        usuario.saldo = (saldo_anterior - monto_total).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        usuario.save()

        # Crear transaccion
        trans = Transaccion.objects.create(
            usuario=usuario,
            tipo='COMPRA',
            accion=accion,
            cantidad=cantidad,
            monto=monto_total,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=usuario.saldo,
            descripcion=f"Compra {accion.nombre} x{cantidad} a ${accion.precio}"
        )

    return Response({
        "detail": "Compra realizada",
        "monto_total": f"{monto_total}",
        "saldo_anterior": f"{saldo_anterior}",
        "saldo_nuevo": f"{usuario.saldo}",
        "portafolio": PortafolioSerializer(portafolio).data,
        "transaccion": TransaccionSerializer(trans).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def vender(request):
    """
    POST /api/vender/
    body: { "id_usuario": 1, "id_accion": 2, "cantidad": 5 }
    """
    data = request.data
    try:
        id_usuario = int(data.get('id_usuario'))
        id_accion = int(data.get('id_accion'))
        cantidad = int(data.get('cantidad'))
    except Exception:
        return Response({"detail": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

    if cantidad <= 0:
        return Response({"detail": "La cantidad debe ser mayor a 0"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    accion = get_object_or_404(Accion, pk=id_accion)

    with transaction.atomic():
        usuario = Usuario.objects.select_for_update().get(pk=usuario.id_usuario)
        saldo_anterior = usuario.saldo

        # Obtener portafolio
        try:
            portafolio = Portafolio.objects.select_for_update().get(usuario=usuario, accion=accion)
        except Portafolio.DoesNotExist:
            return Response({"detail": "No posee esa acción en el portafolio"}, status=status.HTTP_400_BAD_REQUEST)

        if portafolio.cantidad < cantidad:
            return Response({"detail": "Cantidad a vender mayor a la poseída", "posee": portafolio.cantidad}, status=status.HTTP_400_BAD_REQUEST)

        # Monto obtenido por venta
        monto_obtenido = (Decimal(cantidad) * accion.precio).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        # Actualizar portafolio
        portafolio.cantidad = portafolio.cantidad - cantidad
        if portafolio.cantidad == 0:
            portafolio.delete()
            portafolio_serialized = None
        else:
            portafolio.save()
            portafolio_serialized = PortafolioSerializer(portafolio).data

        # Actualizar saldo usuario
        usuario.saldo = (saldo_anterior + monto_obtenido).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        usuario.save()

        # Crear transaccion
        trans = Transaccion.objects.create(
            usuario=usuario,
            tipo='VENTA',
            accion=accion,
            cantidad=cantidad,
            monto=monto_obtenido,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=usuario.saldo,
            descripcion=f"Venta {accion.nombre} x{cantidad} a ${accion.precio}"
        )

    return Response({
        "detail": "Venta realizada",
        "monto_obtenido": f"{monto_obtenido}",
        "saldo_anterior": f"{saldo_anterior}",
        "saldo_nuevo": f"{usuario.saldo}",
        "portafolio": portafolio_serialized,
        "transaccion": TransaccionSerializer(trans).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def depositar(request):
    """
    POST /api/depositar/
    body: { "id_usuario": 1, "id_config": 1 }  -> el monto será tomado desde ConfigMonto (SQL)
    """
    data = request.data
    try:
        id_usuario = int(data.get('id_usuario'))
        id_config = int(data.get('id_config'))
    except Exception:
        return Response({"detail": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    config = get_object_or_404(ConfigMonto, pk=id_config, tipo__iexact='DEPOSITO')

    with transaction.atomic():
        usuario = Usuario.objects.select_for_update().get(pk=usuario.id_usuario)
        saldo_anterior = usuario.saldo
        monto = config.monto.quantize(Decimal('0.01'))
        usuario.saldo = (saldo_anterior + monto).quantize(Decimal('0.01'))
        usuario.save()

        trans = Transaccion.objects.create(
            usuario=usuario,
            tipo='DEPOSITO',
            accion=None,
            cantidad=None,
            monto=monto,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=usuario.saldo,
            descripcion=f"Depósito automático de ${monto} (config #{config.id_config})"
        )

    return Response({
        "detail": "Depósito realizado",
        "monto": f"{monto}",
        "saldo_anterior": f"{saldo_anterior}",
        "saldo_nuevo": f"{usuario.saldo}",
        "transaccion": TransaccionSerializer(trans).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def retirar(request):
    """
    POST /api/retirar/
    body: { "id_usuario": 1, "id_config": 2 } -> monto tomado desde ConfigMonto (SQL)
    """
    data = request.data
    try:
        id_usuario = int(data.get('id_usuario'))
        id_config = int(data.get('id_config'))
    except Exception:
        return Response({"detail": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

    usuario = get_object_or_404(Usuario, pk=id_usuario)
    config = get_object_or_404(ConfigMonto, pk=id_config, tipo__iexact='RETIRO')

    with transaction.atomic():
        usuario = Usuario.objects.select_for_update().get(pk=usuario.id_usuario)
        saldo_anterior = usuario.saldo
        monto = config.monto.quantize(Decimal('0.01'))

        if saldo_anterior < monto:
            return Response({"detail": "Saldo insuficiente para retiro", "saldo_actual": f"{saldo_anterior}"}, status=status.HTTP_400_BAD_REQUEST)

        usuario.saldo = (saldo_anterior - monto).quantize(Decimal('0.01'))
        usuario.save()

        trans = Transaccion.objects.create(
            usuario=usuario,
            tipo='RETIRO',
            accion=None,
            cantidad=None,
            monto=monto,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=usuario.saldo,
            descripcion=f"Retiro automático de ${monto} (config #{config.id_config})"
        )

    return Response({
        "detail": "Retiro realizado",
        "monto": f"{monto}",
        "saldo_anterior": f"{saldo_anterior}",
        "saldo_nuevo": f"{usuario.saldo}",
        "transaccion": TransaccionSerializer(trans).data
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([AllowAny])
def actualizar_usuario(request, pk):
    """
    PUT /api/usuarios/<pk>/actualizar/
    Body: { "nombre": "...", "direccion":"...", "clabe": "...", "cuenta_bancaria":"..." }
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    data = request.data
    serializer = UsuarioSerializer(instance=usuario, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "Usuario actualizado", "usuario": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
