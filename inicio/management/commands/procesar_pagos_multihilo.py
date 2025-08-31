from django.core.management.base import BaseCommand
from inicio.models import Pago
import threading
import queue
import time
from decimal import Decimal
from django.utils import timezone

lock = threading.Lock()
cola = queue.Queue()

def procesar_pago(pago):
    """Marca el pago como pagado y guarda los cambios."""
    with lock:
        time.sleep(0.1)  # simula el tiempo de procesamiento
        pago.estado = 'pagado'
        pago.fecha_pago = timezone.localdate()
        pago.monto_pagado = pago.monto
        pago.metodo_pago = 'efectivo'
        pago.save()
        print(f"[Consumidor] Pago {pago.id} procesado | Monto: {pago.monto}")

def productor():
    # busca pagos pendientes y los añade a la cola
    for pago in Pago.objects.filter(estado='pendiente'):
        print(f"[Productor] Encolando pago {pago.id} por {pago.monto}")
        cola.put(pago)

def consumidor():
    # saca los pagos de la cola y los procesa
    while True:
        try:
            pago = cola.get(timeout=1)
            procesar_pago(pago)
            cola.task_done()
        except queue.Empty:
            break

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Iniciando procesamiento multihilo..."))

        # crear los hilos
        hilo_prod = threading.Thread(target=productor)
        hilo_cons = threading.Thread(target=consumidor)

        hilo_prod.start()
        hilo_cons.start()

        hilo_prod.join()
        hilo_cons.join()

        self.stdout.write(self.style.SUCCESS("Procesamiento multihilo finalizado."))

        # se obtienen todos los montos de pagos
        montos = list(Pago.objects.values_list('monto', flat=True))
        procesados = list(
            map(lambda x: round(x * Decimal('1.1'), 2), filter(lambda x: x > 100, montos))
        )

        self.stdout.write(self.style.SUCCESS(
            f"Montos > 100 con +10% interés: {procesados}"
        ))

        # se ordena de mayor a menor
        ordenados = sorted(procesados, key=lambda x: x, reverse=True)
        self.stdout.write(self.style.SUCCESS(f"Ordenados desc: {ordenados}"))
