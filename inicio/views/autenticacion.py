from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from ..models import PerfilUsuario


def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado:
            login(request, usuario_autenticado)

            if usuario_autenticado.is_superuser:
                return redirect('/admin/')

            try:
                perfil = PerfilUsuario.objects.get(user=usuario_autenticado)

                if perfil.tipo_usuario == 'admin_edificio':
                    return redirect('dashboard_admin')
                elif perfil.tipo_usuario == 'arrendatario':
                    return redirect('dashboard_arrendatario')
                else:
                    messages.error(request, 'Tipo de usuario no reconocido.')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'El perfil del usuario no existe.')
        else:
            messages.error(request, 'Usuario o contraseña inválidos.')

    return render(request, 'inicio/autenticacion/login.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

def admin_logout_redirect(request):
    return cerrar_sesion(request)


