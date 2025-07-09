from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')
        
        usuario_autenticado = authenticate(request, username=usuario, password=clave)
        
        if usuario_autenticado is not None:
            login(request, usuario_autenticado)
            if usuario_autenticado.is_staff:
                return redirect('dashboard_admin')
            else:
                messages.error(request, 'Acceso denegado: no eres administrador.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'inicio/login.html')


def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
    return render(request, 'inicio/contacto.html')

def vista_registrarse(request):
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        usuario = request.POST.get('usuario')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        clave = request.POST.get('clave')

        if User.objects.filter(username=usuario).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
        elif User.objects.filter(email=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
        else:
            nuevo_usuario = User.objects.create_user(
                username=usuario,
                password=clave,
                email=correo,
                first_name=nombre_completo
            )
            nuevo_usuario.last_name = telefono  
            nuevo_usuario.save()
            messages.success(request, 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.')
            return redirect('login')

    return render(request, 'inicio/registrarse.html')

def dashboard_admin(request):
    return render(request, 'inicio/dashboard_admin.html')