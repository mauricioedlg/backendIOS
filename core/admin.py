from django.contrib import admin

# Register your models here.


from .models import Usuario, Accion, Portafolio, Transaccion

admin.site.register(Usuario)
admin.site.register(Accion)
admin.site.register(Portafolio)
admin.site.register(Transaccion)