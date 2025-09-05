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
from django.contrib.auth import update_session_auth_hash
# Iniciar el consumidor de la cola de tareas al cargar la aplicación
from django.shortcuts import render, redirect, get_object_or_404

from .models import PerfilUsuario, Contrato  # Ajusta si tu modelo de propiedad tiene otro nombre

from django.core.paginator import Paginator

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

# -el login y registro--

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import PerfilUsuario

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado:
            login(request, usuario_autenticado)

            # Si es superusuario, va al admin de Django
            if usuario_autenticado.is_superuser:
                return redirect('/admin/')

            try:
                perfil = PerfilUsuario.objects.get(user=usuario_autenticado)

                # Redirección automática según el tipo de usuario
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
    # Solo admins pueden acceder
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    # Capturar parámetros de búsqueda y filtro
    search_query = request.GET.get('search', '').strip()
    estado_filter = request.GET.get('estado', '').strip()

    # Query base
    contratos = Contrato.objects.select_related('arrendatario').order_by('-fecha_inicio')

    # Filtro por búsqueda (usuario o departamento)
    if search_query:
        contratos = contratos.filter(
            Q(arrendatario__username__icontains=search_query) |
            Q(numero_departamento__icontains=search_query)
        )

    # Filtro por estado
    if estado_filter and estado_filter.lower() != 'estado':
        contratos = contratos.filter(estado=estado_filter.lower())

    # Contador de resultados
    total_resultados = contratos.count()

    # Paginación: 10 contratos por página
    paginator = Paginator(contratos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inicio/contratos_admin.html', {
        'contratos': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'estado_filter': estado_filter,
        'total_resultados': total_resultados
    })


@login_required
def crear_contrato(request):
    # Solo admins pueden crear contratos
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        # Recoger datos del formulario
        inquilino_id = request.POST.get('inquilino')
        numero_departamento = request.POST.get('numero_departamento')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        monto = request.POST.get('monto')
        terminos = request.POST.get('condiciones')

        # Validaciones básicas
        if not all([inquilino_id, numero_departamento, fecha_inicio, fecha_fin, monto]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('crear_contrato')

        # Obtener el perfil del arrendatario
        inquilino = get_object_or_404(
            PerfilUsuario, id=inquilino_id, tipo_usuario='arrendatario'
        )

        # Crear el contrato en la base de datos
        Contrato.objects.create(
            arrendatario=inquilino.user,          # Relación con User
            numero_departamento=numero_departamento,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tarifa_mensual=monto,
            terminos_adicionales=terminos,
            estado='activo'
        )

        messages.success(request, 'Contrato creado correctamente.')
        return redirect('contratos_admin')

    # GET: mostrar formulario con lista de arrendatarios
    inquilinos = PerfilUsuario.objects.filter(tipo_usuario='arrendatario')

    return render(request, 'inicio/nuevo_contrato.html', {
        'inquilinos': inquilinos
    })



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


from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from datetime import timedelta
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def pagos_admin(request):
    hoy = timezone.localdate()
    dias_filtro = request.GET.get('vence_en', '')
    estado_filtro = request.GET.get('estado', '')
    contrato_q = request.GET.get('contrato', '').strip()
    arrendatario_q = request.GET.get('arrendatario', '').strip()

    pagos_qs = Pago.objects.select_related('contrato').order_by('fecha_vencimiento')

    # Filtro por estado
    if estado_filtro in ['pendiente', 'pagado', 'vencido']:
        pagos_qs = pagos_qs.filter(estado=estado_filtro)

    # Filtro por rango de vencimiento
    if dias_filtro and dias_filtro.isdigit():
        limite = hoy + timedelta(days=int(dias_filtro))
        pagos_qs = pagos_qs.filter(
            estado='pendiente',
            fecha_vencimiento__range=(hoy, limite)
        )

    # Filtros adicionales
    if contrato_q:
        pagos_qs = pagos_qs.filter(contrato__numero_departamento__icontains=contrato_q)
    if arrendatario_q:
        pagos_qs = pagos_qs.filter(contrato__arrendatario__username__icontains=arrendatario_q)

    # KPIs
    total_pendientes = Pago.objects.filter(estado='pendiente').count()
    total_pagados = Pago.objects.filter(estado='pagado').count()
    total_vencidos = Pago.objects.filter(estado='vencido').count()
    conteo_7 = Pago.objects.filter(
        estado='pendiente',
        fecha_vencimiento__range=(hoy, hoy + timedelta(days=7))
    ).count()

    # Paginación
    paginator = Paginator(pagos_qs, 10)
    page_number = request.GET.get('page')
    pagos = paginator.get_page(page_number)

    return render(request, 'inicio/pagos_admin.html', {
        'pagos': pagos,
        'total_pendientes': total_pendientes,
        'total_pagados': total_pagados,
        'total_vencidos': total_vencidos,
        'conteo_7': conteo_7,
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
def notificaciones_admin(request):
    notificaciones = Notificacion.objects.order_by('-programada_para')
    return render(request, 'inicio/notificaciones_admin.html', {
        'notificaciones': notificaciones
    })


@login_required
def reintentar_notificacion(request, id):
    notificacion = get_object_or_404(Notificacion, id=id)
    # Cambiar estado a pendiente para que el sistema la vuelva a enviar
    notificacion.estado = 'pendiente'
    notificacion.intentos = 0  # o sumar 1 si quieres registrar reintentos
    notificacion.save()

    # Aquí podrías llamar a la función que procesa/envía notificaciones
    # procesar_notificacion(notificacion)

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
    # Aquí iría la lógica para programar una notificación manualmente
    # Por ahora solo redirige a la lista de notificaciones
    messages.info(request, "Función de programación manual aún no implementada.")
    return redirect('notificaciones_admin')



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



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Contrato

@login_required
def detalle_contrato(request, contrato_id):
    # Solo admins o el arrendatario dueño del contrato pueden verlo
    contrato = get_object_or_404(Contrato, id=contrato_id)

    if request.user.perfilusuario.tipo_usuario != 'admin_edificio' and contrato.arrendatario != request.user:
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/detalle_contrato.html', {
        'contrato': contrato
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Contrato

@login_required
def editar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    # Solo admin puede editar
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

    return render(request, 'inicio/editar_contrato.html', {
        'contrato': contrato
    })

@login_required
def eliminar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)

    # Solo admin puede eliminar
    if request.user.perfilusuario.tipo_usuario != 'admin_edificio':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        contrato.delete()
        messages.success(request, 'Contrato eliminado correctamente.')
        return redirect('contratos_admin')

    return render(request, 'inicio/eliminar_contrato.html', {
        'contrato': contrato
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .models import Contrato, Notificacion

@login_required
def contratos_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')
    contratos = Contrato.objects.filter(arrendatario=request.user)
    return render(request, 'inicio/contratos_arrendatario.html', {
        'contratos': contratos
    })

@login_required
def notificaciones_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user
    ).order_by('-programada_para')

    return render(request, 'inicio/notificaciones_arrendatario.html', {
        'notificaciones': notificaciones
    })

@login_required
def dashboard_arrendatario(request):
    # Si no es arrendatario, lo mandamos al dashboard de admin
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    # Obtener el contrato principal del arrendatario (o None si no tiene)
    contrato = Contrato.objects.filter(arrendatario=request.user).first()

    # Notificaciones automáticas del arrendatario (últimas 5)
    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user,
        tipo__in=['recordatorio_pago', 'multa']  # Ajusta según tus tipos reales
    ).order_by('-programada_para')[:5]

    return render(request, 'inicio/dashboard_arrendatario.html', {
        'contrato': contrato,
        'notificaciones': notificaciones
    })

@login_required
def editar_perfil_arrendatario(request):
    # Solo arrendatarios pueden entrar aquí
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_arrendatario')

    if request.method == 'POST':
        # Cambiar username si se envía
        nuevo_username = request.POST.get('username')
        if nuevo_username and nuevo_username != request.user.username:
            request.user.username = nuevo_username

        # Datos básicos
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.perfilusuario.telefono = request.POST.get('telefono', request.user.perfilusuario.telefono)

        # Cambiar contraseña si se envía y no está vacía
        nueva_pass = request.POST.get('password')
        if nueva_pass and nueva_pass.strip():
            request.user.set_password(nueva_pass.strip())
            # Mantener sesión activa después de cambiar contraseña
            update_session_auth_hash(request, request.user)

        # Guardar cambios
        request.user.save()
        request.user.perfilusuario.save()

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/editar_perfil_arrendatario.html', {
        'usuario': request.user
    })

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

@login_required
def contrato_pdf(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id, arrendatario=request.user)

    # Renderizar plantilla HTML a string
    html_string = render_to_string('inicio/contrato_pdf.html', {'contrato': contrato})

    # Crear PDF en memoria
    html = HTML(string=html_string)
    result = html.write_pdf()

    # Respuesta HTTP con el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{contrato.id}.pdf"'
    response.write(result)
    return response