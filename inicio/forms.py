from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.mail import EmailMessage
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class CrearArrendatarioForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Nombre de usuario'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Apellido'
        })
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Teléfono'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Contraseña'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):

        subject = "Instrucciones para restablecer tu contraseña"
        reset_link = f"{context['protocol']}://{context['domain']}/password-reset-confirm/{context['uid']}/{context['token']}/"

        message = (
            f"Hola,\n\n"
            f"Recibiste este correo porque solicitaste restablecer tu contraseña en tu cuenta del sistema de arriendo del Edificio Cartagena.\n\n"
            f"Por favor haz clic en el siguiente enlace para crear una nueva contraseña:\n\n"
            f"{reset_link}\n\n"
            f"Si no solicitaste este cambio, puedes ignorar este mensaje.\n\n"
            f"Saludos,\n"
            f"El equipo de Edificio Cartagena"
        )

        email = EmailMessage(subject, message, from_email, [to_email])
        email.send()


class CustomSetPasswordForm(SetPasswordForm):
    error_messages = {
        'password_mismatch': "Las contraseñas no coinciden.",
    }

    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-400',
            'placeholder': 'Ingresa tu nueva contraseña'
        }),
        help_text="Tu contraseña debe tener al menos 8 caracteres, no ser común ni completamente numérica."
    )

    new_password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-400',
            'placeholder': 'Confirma tu nueva contraseña'
        }),
        help_text="Repite la contraseña para verificar."
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                self.add_error('new_password2', self.error_messages['password_mismatch'])

            try:
                validate_password(password1, self.user)
            except ValidationError as e:
                mensajes = []
                for msg in e.messages:
                    if "This password is too short" in msg:
                        mensajes.append("La contraseña debe tener al menos 8 caracteres.")
                    elif "This password is too common" in msg:
                        mensajes.append("La contraseña es demasiado común.")
                    elif "This password is entirely numeric" in msg:
                        mensajes.append("La contraseña no puede ser solo números.")
                    else:
                        continue
                for mensaje in mensajes:
                    self.add_error('new_password1', mensaje)

        return cleaned_data

class EditarArrendatarioForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Nombre de usuario'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Apellido'
        })
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 '
                     'focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Teléfono'
        })
    )
