import logging
import queue
import threading
import time
from .tareas import enviar_correo_async
from .errores import manejar_error

logger = logging.getLogger(__name__)

cola = queue.Queue()

def productor(tarea):
    logger.info(f"[PRODUCTOR] Encolando tarea: {tarea}")
    cola.put(tarea)

def consumidor():
    while True:
        tarea = cola.get()
        try:
            logger.info(f"[CONSUMIDOR] Procesando tarea: {tarea}")
            if tarea == "Generar reporte de pagos":
                time.sleep(1)  # se simula que se genera el reporte
                enviar_correo_async("administrador_1@gmail.com", "Reporte solicitado", "Adjunto reporte")
        except Exception as e:
            manejar_error("Error procesando tarea", e)
        finally:
            cola.task_done()  #se marca que la tarea ya se hizo

def iniciar_consumidor():
    hilo = threading.Thread(target=consumidor, daemon=True)
    hilo.start()
    logger.info("[COLA] Consumidor iniciado")
