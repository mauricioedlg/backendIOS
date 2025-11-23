from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views
from django.shortcuts import redirect

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'acciones', views.AccionViewSet, basename='accion')
router.register(r'portafolios', views.PortafolioViewSet, basename='portafolio')
router.register(r'transacciones', views.TransaccionViewSet, basename='transaccion')
router.register(r'config-montos', views.ConfigMontoViewSet, basename='configmontos')

urlpatterns = [
    path('', lambda request: redirect('/api/')),     # Redirige la raíz a /api/
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # Endpoints de negocio
    path('api/comprar/', views.comprar, name='comprar'),
    path('api/vender/', views.vender, name='vender'),
    path('api/depositar/', views.depositar, name='depositar'),
    path('api/retirar/', views.retirar, name='retirar'),
    path('api/usuarios/<int:pk>/actualizar/', views.actualizar_usuario, name='actualizar_usuario'),
]
