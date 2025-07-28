from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from inicio.models import PerfilUsuario
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import PerfilUsuario
from django.contrib.auth import logout
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
logger = logging.getLogger(__name__)


def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')
        tipo = request.POST.get('tipo_usuario')  # Ej. 'admin_edificio', 'arrendatario'

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado is not None:
            login(request, usuario_autenticado)

            if usuario_autenticado.is_superuser:
                return redirect('/admin/')  

            try:
                perfil = PerfilUsuario.objects.get(user=usuario_autenticado)

                if perfil.tipo_usuario == tipo:
                    if tipo == 'admin_edificio':
                        return redirect('dashboard_admin')
                    elif tipo == 'arrendatario':
                        return redirect('bienvenida')
                else:
                    messages.error(request, 'Acceso denegado para el tipo de usuario seleccionado')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'El perfil del usuario no existe.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'inicio/login.html')



def vista_registrarse(request):
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        nombre_usuario = request.POST.get('usuario')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        clave = request.POST.get('clave')

        if not all([nombre_completo, nombre_usuario, correo, telefono, clave]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('registrarse')

        if User.objects.filter(username=nombre_usuario).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return redirect('registrarse')

        if User.objects.filter(email=correo).exists():
            messages.error(request, 'Este correo electrónico ya está registrado.')
            return redirect('registrarse')

        try:
            user = User.objects.create_user(
                username=nombre_usuario,
                email=correo,
                password=clave,
                first_name=nombre_completo
            )

            PerfilUsuario.objects.create(
                user=user,
                tipo_usuario='arrendatario',
                telefono=telefono
            )

            messages.success(request, '¡Registro exitoso!')
            return redirect('lista_arrendatarios')  # listado

        except Exception as e:
            logger.error(f'Error en el registro: {str(e)}')
            messages.error(request, 'Ocurrió un error durante el registro. Intenta nuevamente.')

    return render(request, 'inicio/registrarse.html')

@login_required
def lista_arrendatarios(request):
    arrendatarios = PerfilUsuario.objects.filter(tipo_usuario='arrendatario')
    return render(request, 'inicio/lista_arrendatarios.html', {'arrendatarios': arrendatarios})



def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

def dashboard_admin(request):
    return render(request, 'inicio/dashboard_admin.html')



def cerrar_sesion(request):
    logout(request)
    return redirect('bienvenida')


def usuarios_admin(request):
    return render(request, 'inicio/usuarios_admin.html')

def contratos_admin(request):
    return render(request, 'inicio/contratos_admin.html')

def reportes_admin(request):
    return render(request, 'inicio/reportes_admin.html')


