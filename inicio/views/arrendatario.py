from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import timezone
from weasyprint import HTML
from ..models import Contrato, Notificacion, Pago

# Dashboard arrendatario

@login_required
def subir_comprobante_arrendatario(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, contrato__arrendatario=request.user)

    if request.method == 'POST':
        archivo = request.FILES.get('comprobante')
        if archivo:
            pago.comprobante = archivo
            pago.validado = False
            pago.fecha_validacion = None
            pago.save()
            messages.success(request, 'Comprobante subido correctamente.')
            return redirect('pagos_arrendatario')
        else:
            messages.error(request, 'Debes seleccionar un archivo válido.')

    return render(request, 'inicio/arrendatario/subir_comprobante_arrendatario.html', {'pago': pago})

@login_required
def dashboard_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    contrato = Contrato.objects.filter(arrendatario=request.user).first()
    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user,
        tipo__in=['recordatorio_pago', 'multa']
    ).order_by('-programada_para')[:5]

    return render(request, 'inicio/arrendatario/dashboard_arrendatario.html', {
        'contrato': contrato,
        'notificaciones': notificaciones
    })

@login_required
def contratos_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')
    contratos = Contrato.objects.filter(arrendatario=request.user)
    return render(request, 'inicio/arrendatario/contratos_arrendatario.html', {'contratos': contratos})

@login_required
def pagos_arrendatario(request):
    pagos = Pago.objects.filter(contrato__arrendatario=request.user).select_related('contrato').order_by('-fecha_vencimiento')
    return render(request, 'inicio/arrendatario/pagos_arrendatario.html', {'pagos': pagos})


@login_required
def notificaciones_arrendatario(request):
    if request.user.perfilusuario.tipo_usuario != 'arrendatario':
        return redirect('dashboard_admin')

    notificaciones = Notificacion.objects.filter(
        contrato__arrendatario=request.user
    ).order_by('-programada_para')

    return render(request, 'inicio/arrendatario/notificaciones_arrendatario.html', {'notificaciones': notificaciones})

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

        telefono = request.POST.get('telefono', '').strip()
        if not re.fullmatch(r'\d{10}', telefono):
            messages.error(request, 'El número de teléfono debe tener exactamente 10 dígitos.')
            return redirect('editar_perfil_arrendatario')
        request.user.perfilusuario.telefono = telefono

        nueva_pass = request.POST.get('password', '').strip()
        if nueva_pass:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', nueva_pass):
                messages.error(request, 'La contraseña debe incluir al menos un carácter especial.')
                return redirect('editar_perfil_arrendatario')
            request.user.set_password(nueva_pass)
            update_session_auth_hash(request, request.user)

        request.user.save()
        request.user.perfilusuario.save()

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('dashboard_arrendatario')

    return render(request, 'inicio/arrendatario/editar_perfil_arrendatario.html', {'usuario': request.user})

# se genera el contrato
@login_required
def contrato_pdf(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id, arrendatario=request.user)
    html_string = render_to_string('inicio/arrendatario/contrato_pdf.html', {'contrato': contrato})
    html = HTML(string=html_string)
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrato_{contrato.id}.pdf"'
    response.write(result)
    return response
