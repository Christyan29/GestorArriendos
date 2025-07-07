from django.shortcuts import render

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_login(request):
    return render(request, 'inicio/login.html')

def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

def vista_registrarse(request):
    return render(request, 'inicio/registrarse.html')

def dashboard_admin(request):
    return render(request, 'inicio/dashboard_admin.html')