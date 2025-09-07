from datetime import timedelta
import logging
import pandas as pd
import tempfile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

from weasyprint import HTML

from .models import PerfilUsuario, Contrato, Pago, Notificacion
from .cola_tareas import productor, iniciar_consumidor

logger = logging.getLogger(__name__)

# VISTAS PÚBLICAS
def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        mensaje = request.POST.get('mensaje')

        cuerpo = (
            f"Nuevo mensaje de contacto:\n\n"
            f"Nombre: {nombre}\n"
            f"Email: {email}\n"
            f"Teléfono: {telefono}\n"
            f"Mensaje:\n{mensaje}"
        )

        send_mail(
            subject='Nuevo mensaje de contacto - Edificio Cartagena',
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        messages.success(request, '¡Tu mensaje fue enviado con éxito! Pronto te contactaremos por correo.')
        return redirect('contacto')

    return render(request, 'inicio/contacto.html')

#
# LOGIN / LOGOUT / REGISTRO
#

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

    return render(request, 'inicio/login.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('login')  # ahora redirige a tu login personalizado

# Vista para interceptar el logout del admin y usar el mismo flujo
def admin_logout_redirect(request):
    return cerrar_sesion(request)

def crear_admin_view(request):
    if request.method == 'POST':
        return redirect('/admin/')
    return render(request, 'admin/crear_admin_form.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('bienvenida')

def crear_admin_view(request):
    if request.method == 'POST':
        return redirect('/admin/')
    return render(request, 'admin/crear_admin_form.html')


# DASHBOARD ADMIN

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
def reportes_admin(request):
    return render(request, 'inicio/reportes_admin.html')


# CONTRATOS ADMIN

@login_required
def contratos_admin(request):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    search_query = request.GET.get('search', '').strip()
    estado_filter = request.GET.get('estado', '').strip()

    contratos = Contrato.objects.select_related('arrendatario').order_by('-fecha_inicio')

    if search_query:
        contratos = contratos.filter(
            Q(arrendatario__username__icontains=search_query) |
            Q(numero_departamento__icontains=search_query)
        )

    if estado_filter and estado_filter.lower() != 'estado':
        contratos = contratos.filter(estado=estado_filter.lower())

    paginator = Paginator(contratos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inicio/contratos_admin.html', {
        'contratos': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'estado_filter': estado_filter,
        'total_resultados': contratos.count()
    })

@login_required
def crear_contrato(request):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        inquilino_id = request.POST.get('inquilino')
        numero_departamento = request.POST.get('numero_departamento')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        monto = request.POST.get('monto')
        terminos = request.POST.get('condiciones')

        if not all([inquilino_id, numero_departamento, fecha_inicio, fecha_fin, monto]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('crear_contrato')

        inquilino = get_object_or_404(
            PerfilUsuario, id=inquilino_id, tipo_usuario='arrendatario'
        )

        Contrato.objects.create(
            arrendatario=inquilino.user,
            numero_departamento=numero_departamento,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tarifa_mensual=monto,
            terminos_adicionales=terminos,
            estado='activo'
        )

        messages.success(request, 'Contrato creado correctamente.')
        return redirect('contratos_admin')

    inquilinos = PerfilUsuario.objects.filter(tipo_usuario='arrendatario')
    return render(request, 'inicio/nuevo_contrato.html', {'inquilinos': inquilinos})

@login_required
def detalle_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio' and contrato.arrendatario != request.user:
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/detalle_contrato.html', {'contrato': contrato})

@login_required
def editar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        contrato.numero_departamento = request.POST.get('numero_departamento')
        contrato.fecha_inicio = request.POST.get('fecha_inicio')
        contrato.fecha_fin = request.POST.get('fecha_fin')
        contrato.tarifa_mensual = request.POST.get('monto')
        contrato.terminos_adicionales = request.POST.get('condiciones')
        contrato.estado = request.POST.get('estado')
        contrato.save()

        messages.success(request, 'Contrato actualizado correctamente.')
        return redirect('contratos_admin')

    return render(request, 'inicio/editar_contrato.html', {'contrato': contrato})

@login_required
def eliminar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        contrato.delete()
        messages.success(request, 'Contrato eliminado correctamente.')
        return redirect('contratos_admin')

    return render(request, 'inicio/eliminar_contrato.html', {'contrato': contrato})

# PAGOS ADMIN

@login_required
def pagos_admin(request):
    hoy = timezone.localdate()
    dias_filtro = request.GET.get('vence_en', '')
    estado_filtro = request.GET.get('estado', '')
    contrato_q = request.GET.get('contrato', '').strip()
    arrendatario_q = request.GET.get('arrendatario', '').strip()

    pagos_qs = Pago.objects.select_related('contrato').order_by('fecha_vencimiento')

    if estado_filtro in ['pendiente', 'pagado', 'vencido']:
        pagos_qs = pagos_qs.filter(estado=estado_filtro)

    if dias_filtro and dias_filtro.isdigit():
        limite = hoy + timedelta(days=int(dias_filtro))
        pagos_qs = pagos_qs.filter(
            estado='pendiente',
            fecha_vencimiento__range=(hoy, limite)
        )

    if contrato_q:
        pagos_qs = pagos_qs.filter(contrato__numero_departamento__icontains=contrato_q)
    if arrendatario_q:
        pagos_qs = pagos_qs.filter(contrato__arrendatario__username__icontains=arrendatario_q)

    paginator = Paginator(pagos_qs, 10)
    page_number = request.GET.get('page')
    pagos = paginator.get_page(page_number)

    return render(request, 'inicio/pagos_admin.html', {
        'pagos': pagos,
        'total_pendientes': Pago.objects.filter(estado='pendiente').count(),
        'total_pagados': Pago.objects.filter(estado='pagado').count(),
        'total_vencidos': Pago.objects.filter(estado='vencido').count(),
        'conteo_7': Pago.objects.filter(
            estado='pendiente',
            fecha_vencimiento__range=(hoy, hoy + timedelta(days=7))
        ).count(),
        'dias_filtro': dias_filtro,
        'estado_filtro': estado_filtro,
        'contrato_q': contrato_q,
        'arrendatario_q': arrendatario_q
    })

@login_required
def registrar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    if pago.estado != 'pagado':
        pago.estado = 'pagado'
        pago.fecha_pago = timezone.now()
        pago.save()
        messages.success(request, f'El pago {pago.id} se ha registrado como pagado.')
    else:
        messages.info(request, f'El pago {pago.id} ya estaba marcado como pagado.')

    return redirect('pagos_admin')

@login_required
def marcar_vencido(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    if pago.estado != 'vencido':
        pago.estado = 'vencido'
        pago.save()
        messages.warning(request, f'El pago {pago.id} se ha marcado como vencido.')
    else:
        messages.info(request, f'El pago {pago.id} ya estaba marcado como vencido.')

    return redirect('pagos_admin')

@login_required
def exportar_pagos_excel(request):
    pagos = (
        Pago.objects.all()
        .order_by('-monto_pagado')
        .values('contrato__numero_departamento', 'monto_pagado', 'estado')
    )

    df = pd.DataFrame(list(pagos))
    df.insert(1, 'Columna Vacía', None)
    df = df[['contrato__numero_departamento', 'Columna Vacía', 'monto_pagado', 'estado']]
    df['monto_pagado'] = df['monto_pagado'].fillna(0).astype(int)

    df.rename(columns={
        'contrato__numero_departamento': 'Número de Departamento',
        'Columna Vacía': '',
        'monto_pagado': 'Monto Pagado',
        'estado': 'Estado del Pago'
    }, inplace=True)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="pagos.xlsx"'
    df.to_excel(response, index=False)
    return response

# NOTIFICACIONES

@login_required
def notificaciones_admin(request):
    notificaciones = Notificacion.objects.order_by('-programada_para')
    return render(request, 'inicio/notificaciones_admin.html', {'notificaciones': notificaciones})

@login_required
def reintentar_notificacion(request, id):
    notificacion = get_object_or_404(Notificacion, id=id)
    notificacion.estado = 'pendiente'
    notificacion.intentos = 0
    notificacion.save()
    messages.success(request, "Notificación reprogramada para envío.")
    return redirect('notificaciones_admin')

@login_required
def marcar_leida(request, id):
    notificacion = get_object_or_404(Notificacion, id=id)
    notificacion.estado = 'leida'
    notificacion.save()
    messages.success(request, "Notificación marcada como leída.")
    return redirect('notificaciones_admin')

@login_required
def programar_manual(request):
    messages.info(request, "Función de programación manual aún no implementada.")
    return redirect('notificaciones_admin')

def ejecutar_tarea_avanzada(request):
    if request.method == "POST":
        iniciar_consumidor()
        productor("Generar reporte de pagos")
        messages.success(request, "Tarea avanzada encolada y procesándose en segundo plano.")
    return redirect(reverse("dashboard_admin"))


# DASHBOARD ARRENDATARIO

@login_required
def dashboard_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    contrato = Contrato.objects.filter(arrendatario=request.user).first()
    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user,
        tipo__in=['recordatorio_pago', 'multa']
    ).order_by('-programada_para')[:5]

    return render(request, 'inicio/dashboard_arrendatario.html', {
        'contrato': contrato,
        'notificaciones': notificaciones
    })

@login_required
def contratos_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')
    contratos = Contrato.objects.filter(arrendatario=request.user)
    return render(request, 'inicio/contratos_arrendatario.html', {'contratos': contratos})

@login_required
def notificaciones_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user
    ).order_by('-programada_para')

    return render(request, 'inicio/notificaciones_arrendatario.html', {'notificaciones': notificaciones})

@login_required
def editar_perfil_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        nuevo_username = request.POST.get('username')
        if nuevo_username and nuevo_username != request.user.username:
            request.user.username = nuevo_username

        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.perfilusuario.telefono = request.POST.get('telefono', request.user.perfilusuario.telefono)

        nueva_pass = request.POST.get('password')
        if nueva_pass and nueva_pass.strip():
            request.user.set_password(nueva_pass.strip())
            update_session_auth_hash(request, request.user)

        request.user.save()
        request.user.perfilusuario.save()

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/editar_perfil_arrendatario.html', {'usuario': request.user})


# GENERAR CONTRATO PDF
@login_required
def contrato_pdf(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id, arrendatario=request.user)
    html_string = render_to_string('inicio/contrato_pdf.html', {'contrato': contrato})
    html = HTML(string=html_string)
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{contrato.id}.pdf"'
    response.write(result)
    return response
