from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inicio.models import Pago, Contrato, PerfilUsuario
from decimal import Decimal
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = "se crean contratos y pagos de prueba "

    def handle(self, *args, **kwargs):
        # departamentos de prueba
        departamentos = ['1A', '2B', '3C', '4D']

        # Monto y la fecha de vencimiento por departamento
        pagos_info = {
            '1A': (Decimal('200.00'), date(2025, 9, 5)),
            '2B': (Decimal('250.00'), date(2025, 9, 6)),
            '3C': (Decimal('100.00'), date(2025, 9, 7)),
            '4D': (Decimal('300.00'), date(2025, 9, 8)),
        }

        periodo = date(2025, 9, 1)  # periodo de prueba
        creados = 0

        # Se crea un usuario arrendatario
        arrendatario, creado_usuario = User.objects.get_or_create(
            username='arrendatario_prueba',
            defaults={
                'first_name': 'Arrendatario',
                'last_name': 'Perez',
                'email': 'arrendatarioperez@gmail.com',
            }
        )

        perfil, _ = PerfilUsuario.objects.get_or_create(user=arrendatario)
        if perfil.tipo_usuario != 'arrendatario':
            perfil.tipo_usuario = 'arrendatario'
            perfil.save()

        if creado_usuario:
            self.stdout.write(self.style.WARNING("arrendatario_prueba creado"))

        for depto in departamentos:
            # Se usca el contrato activo del arrendatario
            contrato, creado_contrato = Contrato.objects.get_or_create(
                numero_departamento=depto,
                estado='activo',
                defaults={
                    'arrendatario': arrendatario,
                    'fecha_inicio': date(2025, 2, 4),
                    'fecha_fin': date(2025, 8, 31),
                    'tarifa_mensual': Decimal('200.00'),
                    'terminos_adicionales': 'contrato de prueba',
                }
            )
            if creado_contrato:
                self.stdout.write(self.style.WARNING(
                    f"contrato creado para el departamento {depto}"
                ))

            monto, fecha_venc = pagos_info[depto]

            if Pago.objects.filter(contrato=contrato, periodo=periodo).exists():
                self.stdout.write(self.style.WARNING(
                    f"Ya existe un pago para {depto} en {periodo}, se omite"
                ))
                continue

            pago = Pago.objects.create(
                contrato=contrato,
                periodo=periodo,
                fecha_vencimiento=fecha_venc,
                monto=monto,
                estado='pendiente',
                referencia=f"Arriendo de septiembre -Departamento {depto}, Edificio Cartagena"
            )
            creados += 1
            self.stdout.write(self.style.SUCCESS(
                f"Pago creado: ID={pago.id} | {pago.referencia} | Monto={pago.monto} | Estado={pago.estado}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Pagos de prueba creados: {creados}"
        ))
