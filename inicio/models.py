from django.utils import timezone

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.utils import timezone
from datetime import date, datetime, timedelta
import calendar


class EnlaceCrearAdmin(models.Model):
    class Meta:
        managed = False
        verbose_name = "Crear Administrador"
        verbose_name_plural = "Crear Administrador"

# --- perfil de usario---

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin_edificio', 'Administrador del Edificio'),
        ('arrendatario', 'Arrendatario'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_usuario_display()}"

# --contratos ---

class Contrato(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]

    arrendatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='contratos')
    numero_departamento = models.CharField(max_length=20, db_index=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tarifa_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    terminos_adicionales = models.TextField(max_length=1000, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='pendiente')

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(fecha_fin__gt=F('fecha_inicio')), name='contrato_fecha_fin_gt_inicio'),
            models.CheckConstraint(check=Q(tarifa_mensual__gt=0), name='contrato_tarifa_mensual_positive'),
            models.UniqueConstraint(fields=['numero_departamento'], condition=Q(estado='activo'), name='unique_departamento_contrato_activo'),
        ]
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['numero_departamento', 'estado']),
        ]

    def __str__(self):
        return f"Contrato {self.id} • Depto {self.numero_departamento} • {self.arrendatario}"

    def clean(self):
        perfil = getattr(self.arrendatario, 'perfilusuario', None)
        if not perfil or perfil.tipo_usuario != 'arrendatario':
            raise ValidationError({'arrendatario': 'El usuario debe ser de tipo "Arrendatario".'})
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError({'fecha_fin': 'La fecha de fin debe ser mayor que la fecha de inicio.'})
        if self.tarifa_mensual is not None and self.tarifa_mensual <= 0:
            raise ValidationError({'tarifa_mensual': 'La tarifa mensual debe ser positiva.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.generar_calendario_pagos()
            self.programar_notificacion_fin_contrato()

    @staticmethod
    def _add_months(d: date, months: int) -> date:
        month = d.month - 1 + months
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def generar_calendario_pagos(self):
        cursor = date(self.fecha_inicio.year, self.fecha_inicio.month, 1)
        fin_periodo = date(self.fecha_fin.year, self.fecha_fin.month, 1)

        while cursor <= fin_periodo:
            ultimo_dia = calendar.monthrange(cursor.year, cursor.month)[1]
            dia_venc = min(self.fecha_inicio.day, ultimo_dia)
            fecha_venc = date(cursor.year, cursor.month, dia_venc)
            periodo = date(cursor.year, cursor.month, 1)

            Pago.objects.get_or_create(
                contrato=self,
                periodo=periodo,
                defaults={
                    'fecha_vencimiento': fecha_venc,
                    'monto': self.tarifa_mensual,
                    'estado': 'pendiente',
                }
            )

            Pago.programar_notificaciones_para_cuota(self.arrendatario, self, periodo, fecha_venc)
            cursor = self._add_months(cursor, 1)

    def programar_notificacion_fin_contrato(self):
        alerta_dt = datetime.combine(self.fecha_fin - timedelta(days=30), datetime.min.time()).replace(hour=8, minute=0)
        Notificacion.objects.get_or_create(
            usuario=self.arrendatario,
            contrato=self,
            tipo='fin_contrato',
            programada_para=timezone.make_aware(alerta_dt),
            defaults={
                'asunto': f'Fin de contrato próximo - Depto {self.numero_departamento}',
                'cuerpo': 'Tu contrato finalizará en 30 días. Revisa opciones o contacta al administrador.',
                'canal': 'email',
            }
        )

# --pagos -

class Pago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
    ]

    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name='pagos')
    periodo = models.DateField()
    fecha_vencimiento = models.DateField(db_index=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente', db_index=True)

    fecha_pago = models.DateField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, null=True, blank=True)
    referencia = models.CharField(max_length=120, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(monto__gt=0), name='pago_monto_positive'),
            models.UniqueConstraint(fields=['contrato', 'periodo'], name='unique_pago_contrato_periodo'),
        ]
        indexes = [
            models.Index(fields=['contrato', 'estado']),
            models.Index(fields=['periodo']),
        ]

    def __str__(self):
        ym = self.periodo.strftime('%Y-%m')
        return f"Pago {ym} • Depto {self.contrato.numero_departamento} • {self.get_estado_display()}"

    def clean(self):
        errors = {}
        if self.monto is not None and self.monto <= 0:
            errors['monto'] = 'El monto debe ser positivo.'
        if self.estado == 'pagado':
            if not self.fecha_pago:
                errors['fecha_pago'] = 'Debe registrar la fecha de pago.'
            if not self.monto_pagado or self.monto_pagado <= 0:
                errors['monto_pagado'] = 'Debe registrar el monto pagado.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        hoy = timezone.localdate()
        if self.fecha_pago:
            self.estado = 'pagado'
            if not self.monto_pagado:
                self.monto_pagado = self.monto
        elif self.estado != 'pagado':
            self.estado = 'vencido' if hoy > self.fecha_vencimiento else 'pendiente'
        super().save(*args, **kwargs)

    @staticmethod
    def programar_notificaciones_para_cuota(usuario, contrato, periodo, fecha_vencimiento):
        tz = timezone.get_current_timezone()

        dt_recordatorio = datetime.combine(fecha_vencimiento - timedelta(days=5), datetime.min.time()).replace(hour=8)
        Notificacion.objects.get_or_create(
            usuario=usuario,
            contrato=contrato,
            pago=Pago.objects.filter(contrato=contrato, periodo=periodo).first(),
            tipo='recordatorio_pago',
            programada_para=timezone.make_aware(dt_recordatorio, tz),
            defaults={
                'asunto': f'Recordatorio de pago {periodo.strftime("%Y-%m")} • Depto {contrato.numero_departamento}',
                'cuerpo': 'Tienes un pago próximo a vencer en 5 días.',
                'canal': 'email',
            }
        )

        dt_vencido = datetime.combine(fecha_vencimiento + timedelta(days=1), datetime.min.time()).replace(hour=8)

#---notificaciones----
class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('recordatorio_pago', 'Recordatorio de pago'),
        ('pago_vencido', 'Pago vencido'),
        ('fin_contrato', 'Fin de contrato'),
    ]
    CANAL_CHOICES = [
        ('email', 'Correo electrónico'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    pago = models.ForeignKey('Pago', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, db_index=True)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, default='email')

    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()

    programada_para = models.DateTimeField(db_index=True)
    enviada_en = models.DateTimeField(null=True, blank=True)
    enviada = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'enviada', 'leida']),
            models.Index(fields=['tipo', 'programada_para']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['pago', 'tipo'], condition=Q(pago__isnull=False), name='unique_notif_por_pago_tipo'),
            models.UniqueConstraint(fields=['contrato', 'tipo'], condition=Q(contrato__isnull=False) & Q(tipo='fin_contrato'), name='unique_notif_fin_contrato'),
        ]

    def __str__(self):
        base = f"{self.get_tipo_display()} • {self.usuario}"
        if self.contrato_id:
            base += f" • Depto {self.contrato.numero_departamento}"
        return base

    def clean(self):
        if self.tipo in ('recordatorio_pago', 'pago_vencido') and not self.pago_id:
            raise ValidationError({'pago': 'Esta notificación requiere una cuota de pago asociada.'})
        if self.tipo == 'fin_contrato' and not self.contrato_id:
            raise ValidationError({'contrato': 'Esta notificación requiere un contrato asociado.'})
