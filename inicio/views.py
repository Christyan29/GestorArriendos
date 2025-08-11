from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from django.contrib.auth.models import User
from .models import PerfilUsuario, Contrato, Pago, Notificacion

import logging
logger = logging.getLogger(__name__)

# ---------------------------- VISTAS PÚBLICAS ----------------------------

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

# ---------------------------- LOGIN Y REGISTRO ----------------------------

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')
        tipo = request.POST.get('tipo_usuario')  # admin_edificio o arrendatario

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado:
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
                    messages.error(request, 'Tipo de usuario incorrecto para este acceso.')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'El perfil del usuario no existe.')
        else:
            messages.error(request, 'Usuario o contraseña inválidos.')

    return render(request, 'inicio/login.html')

def vista_registrarse(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        nombre_usuario = request.POST.get('usuario')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        clave = request.POST.get('clave')
        confirmar_clave = request.POST.get('confirmar_clave')

        if not all([nombre, apellido, nombre_usuario, correo, telefono, clave, confirmar_clave]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('registrarse')

        if clave != confirmar_clave:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('registrarse')

        if User.objects.filter(username=nombre_usuario).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('registrarse')

        if User.objects.filter(email=correo).exists():
            messages.error(request, 'Este correo ya está registrado.')
            return redirect('registrarse')

        try:
            user = User.objects.create_user(
                username=nombre_usuario,
                email=correo,
                password=clave,
                first_name=nombre,
                last_name=apellido
            )

            PerfilUsuario.objects.create(
                user=user,
                tipo_usuario='arrendatario',
                telefono=telefono
            )

            messages.success(request, '¡Registro exitoso!')
            return redirect('lista_arrendatarios')

        except Exception as e:
            logger.error(f'Error en el registro: {str(e)}')
            messages.error(request, 'Ocurrió un error. Intenta nuevamente.')

    return render(request, 'inicio/registrarse.html')

# ---------------------------- PANEL ADMINISTRATIVO ----------------------------

@login_required
def dashboard_admin(request):
    total_contratos = Contrato.objects.filter(estado='activo').count()
    pagos_pendientes = Pago.objects.filter(estado='pendiente').count()

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=30)
    vencimientos_30d = Pago.objects.filter(
        fecha_vencimiento__lte=limite,
        estado='pendiente'
    ).count()

    notificaciones = Notificacion.objects.order_by('-programada_para')[:5]

    return render(request, 'dashboard_admin.html', {
        'total_contratos': total_contratos,
        'pagos_pendientes': pagos_pendientes,
        'vencimientos_30d': vencimientos_30d,
        'notificaciones': notificaciones
    })

@login_required
def lista_arrendatarios(request):
    arrendatarios = PerfilUsuario.objects.filter(tipo_usuario='arrendatario')
    return render(request, 'inicio/lista_arrendatarios.html', {'arrendatarios': arrendatarios})

@login_required
def usuarios_admin(request):
    return render(request, 'inicio/usuarios_admin.html')

@login_required
def contratos_admin(request):
    return render(request, 'inicio/contratos_admin.html')

@login_required
def reportes_admin(request):
    return render(request, 'inicio/reportes_admin.html')

# ---------------------------- CERRAR SESIÓN ----------------------------

def cerrar_sesion(request):
    logout(request)
    return redirect('bienvenida')



def crear_admin_view(request):
    if request.method == 'POST':
        return redirect('/admin/')

    return render(request, 'admin/crear_admin_form.html')