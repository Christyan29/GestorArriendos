from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from inicio.models import PerfilUsuario

def bienvenida(request):
    return render(request, 'inicio/bienvenida.html')

def vista_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')
        tipo = request.POST.get('tipo_usuario') 

        usuario_autenticado = authenticate(request, username=usuario, password=clave)

        if usuario_autenticado is not None:
            login(request, usuario_autenticado)

            if usuario_autenticado.is_superuser:
                return redirect('/admin/')
            else:
                try:
                    perfil = PerfilUsuario.objects.get(user=usuario_autenticado)

                    if tipo == 'admin' and perfil.tipo_usuario == 'admin_edificio':
                        return redirect('dashboard_admin')
                    elif tipo == 'arrendatario' and perfil.tipo_usuario == 'arrendatario':
                        return redirect('bienvenida')
                    else:
                        messages.error(request, 'Acceso denegado para el tipo de usuario seleccionado.')
                except PerfilUsuario.DoesNotExist:
                    messages.error(request, 'Perfil no encontrado.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

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

        try:
            user = User.objects.create_user(
                username=nombre_usuario,
                email=correo,
                password=clave,
                first_name=nombre_completo
            )
            user.save()

            PerfilUsuario.objects.create(
                user=user,
                tipo_usuario='arrendatario',
                telefono=telefono
            )

            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')

    return render(request, 'inicio/registrarse.html')


def vista_nosotros(request):
    return render(request, 'inicio/nosotros.html')

def vista_contacto(request):

    return render(request, 'inicio/contacto.html')



def dashboard_arrendatarios(request):
    return render(request, 'inicio/dashboard_arrendatarios.html')