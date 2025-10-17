from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import UsuarioViewSet, AccionViewSet, PortafolioViewSet, TransaccionViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'acciones', AccionViewSet)
router.register(r'portafolios', PortafolioViewSet)
router.register(r'transacciones', TransaccionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]