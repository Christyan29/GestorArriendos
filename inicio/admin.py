from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_usuario', 'telefono')
    list_filter = ('tipo_usuario',)
    search_fields = ('user__username', 'telefono')

