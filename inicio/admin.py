from django.contrib import admin
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from .models import PerfilUsuario
from inicio.utils.crear_admin_logic import crear_admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import EnlaceCrearAdmin


class EnlaceCrearAdminAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('crear_admin'))

admin.site.register(EnlaceCrearAdmin, EnlaceCrearAdminAdmin)

class CrearAdminForm(forms.Form):
    usuario = forms.CharField()
    email = forms.EmailField()
    telefono = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, required=False)

class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_usuario', 'telefono')
    list_filter = ('tipo_usuario',)
    search_fields = ('user__username', 'telefono')
    change_list_template = 'admin/crear_admin_form.html'

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path('crear-admin/', self.admin_site.admin_view(self.crear_admin_view))
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

        return render(request, 'admin/crear_admin_form.html', {'form': form, 'mensaje': mensaje})

admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)
