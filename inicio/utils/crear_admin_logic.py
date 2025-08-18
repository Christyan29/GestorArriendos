from django.contrib.auth.models import User
from inicio.models import PerfilUsuario

def crear_admin(usuario, email, telefono, password='Admin#2025'):
    if User.objects.filter(username=usuario).exists():
        return f' El usuario "{usuario}" ya existe.'

    user = User.objects.create_user(
        username=usuario,
        email=email,
        password=password,
        is_staff=True
    )

    PerfilUsuario.objects.create(
        user=user,
        tipo_usuario='admin_edificio',
        telefono=telefono
    )

    return f' Usuario "{usuario}" creado como administrador del edificio.'
