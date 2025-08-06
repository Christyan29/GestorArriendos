from django.db import models
from django.contrib.auth.models import User

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

class Contrato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contrato')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    documento = models.FileField(upload_to='contrato/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

class Pago(models.Model):
    arrendatario = models.ForeignKey(User, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

class Notificacion(models.Model):
    arrendatario = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.arrendatario.username}"
