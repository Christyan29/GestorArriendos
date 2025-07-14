from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
<<<<<<< HEAD
=======
from inicio.models import PerfilUsuario
>>>>>>> main

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')
<<<<<<< HEAD
        
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


=======
        tipo = request.POST.get('tipo_usuario') 

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado is not None:
            login(request, usuario_autenticado)

            if usuario_autenticado.is_superuser:
                return redirect('/admin/')
            else:
                perfil = PerfilUsuario.objects.get(user=usuario_autenticado)
                if perfil.tipo_usuario == 'admin_edificio':
                    return redirect('dashboard_admin')
                elif perfil.tipo_usuario == 'arrendatario':
                    return redirect('bienvenida')

        else:
            messages.error(request, 'Credenciales incorrectas.')

    return render(request, 'inicio/login.html')


def vista_registrarse(request):
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        nombre_usuario = request.POST.get('usuario')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        clave = request.POST.get('clave')

        if User.objects.filter(username=nombre_usuario).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return redirect('registrarse')

        user = User.objects.create_user(
            username=nombre_usuario,
            email=correo,
            password=clave,
            first_name=nombre_completo
        )
        user.save()

        # Siempre se debe registra como arrendatario
        PerfilUsuario.objects.create(
            user=user,
            tipo_usuario='arrendatario',
            telefono=telefono
        )

        messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'inicio/registrarse.html')


>>>>>>> main
def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):
<<<<<<< HEAD
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
=======
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        mensaje = request.POST.get('mensaje')

        if nombre and email and mensaje:
            messages.success(request, 'Gracias por contactarnos. Te responderemos pronto.')
        else:
            messages.error(request, 'Por favor completa todos los campos.')

    return render(request, 'inicio/contacto.html')
>>>>>>> main

def dashboard_admin(request):
    return render(request, 'inicio/dashboard_admin.html')