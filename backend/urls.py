from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import UsuarioViewSet, AccionViewSet, PortafolioViewSet, TransaccionViewSet
from django.shortcuts import redirect

# Registrar los endpoints en el router
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'acciones', AccionViewSet)
router.register(r'portafolios', PortafolioViewSet)
router.register(r'transacciones', TransaccionViewSet)

# Rutas principales
urlpatterns = [
    path('', lambda request: redirect('/api/')),     # Redirige la raíz a /api/
    path('admin/', admin.site.urls),                 # Panel de administración
    path('api/', include(router.urls)),              # Incluye el router con tus endpoints
]