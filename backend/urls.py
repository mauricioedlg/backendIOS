# backend/urls.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    UsuarioViewSet, AccionViewSet, PortafolioViewSet, TransaccionViewSet,
    login, obtener_portafolio_usuario, comprar_accion, vender_accion,
    depositar_retiro, editar_usuario
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'acciones', AccionViewSet)
router.register(r'portafolios', PortafolioViewSet)
router.register(r'transacciones', TransaccionViewSet)

urlpatterns = [
    path('', lambda request: redirect('/api/')),  # si ya lo tenías, mantenlo
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # Endpoints personalizados
    path('api/login/', login, name='api-login'),
    path('api/portafolio/<int:id_usuario>/', obtener_portafolio_usuario, name='api-portafolio'),
    path('api/comprar/', comprar_accion, name='api-comprar'),
    path('api/vender/', vender_accion, name='api-vender'),
    path('api/depositar_retirar/', depositar_retiro, name='api-depositar-retiro'),
    path('api/usuario/editar/<int:id_usuario>/', editar_usuario, name='api-editar-usuario'),
]
