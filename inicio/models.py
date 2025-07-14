<<<<<<< HEAD
from django.db import models

# Create your models here.
=======
from django.contrib.auth.models import User
from django.db import models

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin_edificio', 'Administrador del Edificio'),
        ('arrendatario', 'Arrendatario'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_usuario_display()}"
>>>>>>> main
