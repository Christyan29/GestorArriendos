from django import forms
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import admin
from django.utils.html import format_html

from .models import PerfilUsuario, EnlaceCrearAdmin
from inicio.utils.crear_admin_logic import crear_admin

# admin personalizado
class MyAdminSite(admin.AdminSite):
    site_header = "Administración de Django"
    site_title = "Panel de Administración"
    index_title = "Bienvenido al panel"

    def logout(self, request, extra_context=None):
        logout(request)
        return redirect('login')

my_admin_site = MyAdminSite(name='myadmin')

# Model de Admin para el enlace crearadmin
class EnlaceCrearAdminAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('admin:inicio_perfilusuario_crear-admin'))



# formulario para crear admin
class CrearAdminForm(forms.Form):
    usuario = forms.CharField()
    email = forms.EmailField()
    telefono = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, required=False)

# modelo de admin para Perfilusuario
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_usuario', 'telefono', 'boton_crear_admin')
    list_filter = ('tipo_usuario',)
    search_fields = ('user__username', 'telefono')

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                'crear-admin/',
                self.admin_site.admin_view(self.crear_admin_view),
                name='inicio_perfilusuario_crear-admin'
            )
        ]
        return extra + urls

    def crear_admin_view(self, request):
        mensaje = ''
        if request.method == 'POST':
            form = CrearAdminForm(request.POST)
            if form.is_valid():
                mensaje = crear_admin(
                    form.cleaned_data['usuario'],
                    form.cleaned_data['email'],
                    form.cleaned_data['telefono'],
                    form.cleaned_data.get('password', 'Intesud_2000')
                )
        else:
            form = CrearAdminForm()

        return render(request, 'inicio/autenticacion/crear_admin_form.html', {
            'form': form,
            'mensaje': mensaje
        })

    def boton_crear_admin(self, obj=None):
        url = reverse('admin:inicio_perfilusuario_crear-admin')
        return format_html('<a class="button" href="{}">➕ Crear administrador</a>', url)
    boton_crear_admin.short_description = "Crear Admin"

# registrar modelos en el admin personalizado
my_admin_site.register(EnlaceCrearAdmin, EnlaceCrearAdminAdmin)
my_admin_site.register(PerfilUsuario, PerfilUsuarioAdmin)
