import os
from django.core.exceptions import ValidationError

def validar_extension(archivo):
    """
    Valida que el archivo tenga una extensión permitida.
    Extensiones válidas: .pdf, .jpg, .jpeg, .png
    """
    ext = os.path.splitext(archivo.name)[1].lower()
    extensiones_permitidas = ['.pdf', '.jpg', '.jpeg', '.png']
    if ext not in extensiones_permitidas:
        raise ValidationError(
            f'Extensiones permitidas: {", ".join(extensiones_permitidas)}'
        )

def validar_tamano(archivo):
    """
    Valida que el archivo no supere el tamaño máximo permitido.
    Límite: 10 MB
    """
    limite_mb = 10
    if archivo.size > limite_mb * 1024 * 1024:
        raise ValidationError(
            f'El tamaño máximo permitido es {limite_mb} MB'
        )
