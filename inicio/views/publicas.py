from datetime import timedelta
import logging
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

logger = logging.getLogger(__name__)

def bienvenida(request):
    return render(request, 'inicio/publicas/bienvenida.html')

def vista_nosotros(request):
    return render(request, 'inicio/publicas/nosotros.html')

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

    return render(request, 'inicio/publicas/contacto.html')
