from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.contrib.auth.models import User
from .models import PerfilUsuario, Contrato, Pago, Notificacion
import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Pago
import logging
logger = logging.getLogger(__name__)
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .cola_tareas import productor, iniciar_consumidor
# Iniciar el consumidor de la cola de tareas al cargar la aplicación

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

# -el login y registro--

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

# -- panle de administrador --

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

    return render(request, 'inicio/dashboard_admin.html', {
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

def crear_contrato(request):
    return render(request, 'inicio/crear_contrato.html')

@login_required
def reportes_admin(request):
    return render(request, 'inicio/reportes_admin.html')

# -- cerrar la secion  --

def cerrar_sesion(request):
    logout(request)
    return redirect('bienvenida')

def crear_admin_view(request):
    if request.method == 'POST':
        return redirect('/admin/')

    return render(request, 'admin/crear_admin_form.html')

@login_required
def admin_buscar(request):
    query = request.GET.get('q', '').strip()

    usuarios_result = contratos_result = pagos_result = []

    if query:
        usuarios_result = PerfilUsuario.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(telefono__icontains=query)
        )

        contratos_result = Contrato.objects.filter(
            Q(numero__icontains=query) |
            Q(cliente__user__first_name__icontains=query) |
            Q(cliente__user__last_name__icontains=query)
        )

        pagos_result = Pago.objects.filter(
            Q(id__icontains=query) |
            Q(contrato__numero__icontains=query) |
            Q(monto__icontains=query)
        )

    contexto = {
        'query': query,
        'usuarios_result': usuarios_result,
        'contratos_result': contratos_result,
        'pagos_result': pagos_result
    }
    return render(request, 'inicio/admin_buscar.html', contexto)

@login_required
def vencimientos_admin(request):
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=30)

    vencimientos = Pago.objects.filter(
        fecha_vencimiento__lte=limite,
        estado='pendiente'
    ).select_related('contrato')

    return render(request, 'inicio/vencimientos_admin.html', {
        'vencimientos': vencimientos,
        'hoy': hoy,
        'limite': limite
    })

@login_required
def pagos_admin(request):
    pagos_pendientes = Pago.objects.filter(estado='pendiente').select_related('contrato')
    return render(request, 'inicio/pagos_admin.html', {
        'pagos_pendientes': pagos_pendientes
    })

@login_required
def notificaciones_admin(request):
    notificaciones = Notificacion.objects.order_by('-programada_para')
    return render(request, 'inicio/notificaciones_admin.html', {
        'notificaciones': notificaciones
    })


@login_required
def exportar_pagos_excel(request):
    # Pagos ordenados por monto (mayor primero)
    pagos = (
        Pago.objects.all()
        .order_by('-monto_pagado')
        .values(
            'contrato__numero_departamento',
            'monto_pagado',
            'estado'
        )
    )

    df = pd.DataFrame(list(pagos))

    df.insert(1, 'Columna Vacía', None)  # Columna B vacía
    df = df[['contrato__numero_departamento', 'Columna Vacía', 'monto_pagado', 'estado']]
    df['monto_pagado'] = df['monto_pagado'].fillna(0).astype(int)

    df.rename(columns={
        'contrato__numero_departamento': 'Número de Departamento',
        'Columna Vacía': '',
        'monto_pagado': 'Monto Pagado',
        'estado': 'Estado del Pago'
    }, inplace=True)

    # Respuesta HTTP con archivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pagos.xlsx"'
    df.to_excel(response, index=False)
    return response


def ejecutar_tarea_avanzada(request):
    if request.method == "POST":
        iniciar_consumidor()
        productor("Generar reporte de pagos")
        messages.success(request, "Tarea avanzada encolada y procesándose en segundo plano.")
    return redirect(reverse("dashboard_admin"))
