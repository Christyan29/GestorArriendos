import pandas as pd
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Contrato, Pago, Notificacion, PerfilUsuario  # <-- relativo, incluye PerfilUsuario
from ..cola_tareas import productor, iniciar_consumidor  # <-- relativo
from ..forms import CrearArrendatarioForm  # <-- importa el formulario

from django.contrib.auth import get_user_model
User = get_user_model()
from inicio.forms import EditarArrendatarioForm

# dashboard admin
@login_required
def crear_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        form = CrearArrendatarioForm(request.POST)
        if form.is_valid():
            # se crea el usuario
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_active=True
            )
            # perfil como arrendatario
            PerfilUsuario.objects.create(
                user=user,
                tipo_usuario='arrendatario',
                telefono=form.cleaned_data['telefono']
            )
            messages.success(request, f"Arrendatario {user.username} creado correctamente.")
            return redirect('lista_arrendatarios')
    else:
        form = CrearArrendatarioForm()

    return render(request, 'inicio/admin/crear_arrendatario.html', {'form': form})


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

    return render(request, 'inicio/admin/dashboard_admin.html', {
        'total_contratos': total_contratos,
        'pagos_pendientes': pagos_pendientes,
        'vencimientos_30d': vencimientos_30d,
        'notificaciones': notificaciones
    })

@login_required
def lista_arrendatarios(request):
    arrendatarios = PerfilUsuario.objects.filter(tipo_usuario='arrendatario')
    return render(request, 'inicio/admin/lista_arrendatarios.html', {'arrendatarios': arrendatarios})

@login_required
def usuarios_admin(request):
    return render(request, 'inicio/admin/usuarios_admin.html')

@login_required
def reportes_admin(request):
    return render(request, 'inicio/admin/reportes_admin.html')


# Contratos admin

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

    return render(request, 'inicio/admin/contratos_admin.html', {
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
    return render(request, 'inicio/admin/nuevo_contrato.html', {'inquilinos': inquilinos})

@login_required
def detalle_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio' and contrato.arrendatario != request.user:
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/admin/detalle_contrato.html', {'contrato': contrato})

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

    return render(request, 'inicio/admin/editar_contrato.html', {'contrato': contrato})

@login_required
def eliminar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        contrato.delete()
        messages.success(request, 'Contrato eliminado correctamente.')
        return redirect('contratos_admin')

    return render(request, 'inicio/admin/eliminar_contrato.html', {'contrato': contrato})


# pagos administrador
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

    return render(request, 'inicio/admin/pagos_admin.html', {
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
def subir_comprobante_admin(request, pago_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    pago = get_object_or_404(Pago, id=pago_id)

    if request.method == 'POST':
        archivo = request.FILES.get('comprobante')
        if archivo:
            pago.comprobante = archivo
            pago.validado = False
            pago.fecha_validacion = None
            pago.save()
            messages.success(request, 'Comprobante subido correctamente.')
            return redirect('pagos_admin')
        else:
            messages.error(request, 'Debes seleccionar un archivo válido.')

    return render(request, 'inicio/admin/subir_comprobante_admin.html', {'pago': pago})



@login_required
def validar_comprobante(request, pago_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    pago = get_object_or_404(Pago, id=pago_id)

    if pago.comprobante:
        pago.validado = True
        pago.fecha_validacion = timezone.now()
        pago.validado_por = request.user  #se registra el administrador que valido
        pago.save()
        messages.success(request, f'Comprobante del pago {pago.id} validado correctamente.')
    else:
        messages.error(request, 'No hay comprobante para validar.')

    return redirect('pagos_admin')

@login_required
def rechazar_comprobante(request, pago_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    pago = get_object_or_404(Pago, id=pago_id)

    if pago.comprobante:
        pago.validado = False
        pago.fecha_validacion = None
        pago.save()
        messages.warning(request, f'Comprobante del pago {pago.id} rechazado.')
    else:
        messages.error(request, 'No hay comprobante para rechazar.')

    return redirect('pagos_admin')


@login_required
def registrar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    if pago.estado != 'pagado':
        pago.estado = 'pagado'
        pago.fecha_pago = timezone.now()

        #el monto_pagado debe tener un valor
        if not getattr(pago, 'monto_pagado', None):
            pago.monto_pagado = pago.monto

        pago.save()
        messages.success(
            request,
            f'El pago {pago.id} se ha registrado como pagado por {pago.monto_pagado}.'
        )
    else:
        messages.info(
            request,
            f'El pago {pago.id} ya estaba marcado como pagado.'
        )

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


# Notificaciones admin

@login_required
def notificaciones_admin(request):
    notificaciones = Notificacion.objects.order_by('-programada_para')
    return render(request, 'inicio/admin/notificaciones_admin.html', {'notificaciones': notificaciones})

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
    return render(request, "inicio/admin/tarea_avanzada.html")

@login_required
def historial_validaciones(request):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    pagos_validados = Pago.objects.select_related('contrato', 'validado_por')\
        .filter(validado=True)\
        .order_by('-fecha_validacion')

    return render(request, 'inicio/admin/historial_validaciones.html', {
        'pagos_validados': pagos_validados
    })

@login_required
def lista_arrendatarios(request):
    # solo el admin del edificio puede ver
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    estado = request.GET.get('estado', 'activos')
    q = request.GET.get('q', '').strip()

    base_qs = PerfilUsuario.objects.filter(tipo_usuario='arrendatario').select_related('user')

    if estado == 'inactivos':
        base_qs = base_qs.filter(user__is_active=False)
    else:
        base_qs = base_qs.filter(user__is_active=True)

    if q:
        base_qs = base_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(telefono__icontains=q)
        )

    return render(request, 'inicio/admin/lista_arrendatarios.html', {
        'arrendatarios': base_qs.order_by('user__username'),
        'estado': estado,
        'q': q,
    })


@login_required
def activar_arrendatario(request, user_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    user = get_object_or_404(User, id=user_id, perfilusuario__tipo_usuario='arrendatario')
    user.is_active = True
    user.save(update_fields=['is_active'])
    messages.success(request, f'Arrendatario {user.username} activado.')
    return redirect('lista_arrendatarios')


@login_required
def desactivar_arrendatario(request, user_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    user = get_object_or_404(User, id=user_id, perfilusuario__tipo_usuario='arrendatario')
    user.is_active = False
    user.save(update_fields=['is_active'])
    messages.warning(request, f'Arrendatario {user.username} desactivado.')
    return redirect('lista_arrendatarios')

@login_required
def editar_arrendatario(request, user_id):
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    user = get_object_or_404(User, id=user_id, perfilusuario__tipo_usuario='arrendatario')

    if request.method == 'POST':
        form = EditarArrendatarioForm(request.POST)
        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.perfilusuario.telefono = form.cleaned_data['telefono']
            user.save()
            user.perfilusuario.save()
            messages.success(request, f"Arrendatario {user.username} actualizado correctamente.")
            return redirect('lista_arrendatarios')
        else:
            messages.error(request, "Por favor corrige los errores indicados.")
    else:
        form = EditarArrendatarioForm(initial={
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'telefono': user.perfilusuario.telefono
        })

    return render(request, 'inicio/admin/editar_arrendatario.html', {
        'form': form,
        'user_obj': user
    })
