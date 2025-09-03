import logging
import queue
import threading
import time
from .tareas import enviar_correo_async
from .errores import manejar_error

logger = logging.getLogger(__name__)

cola = queue.Queue()  # aqui se guardan las tareas que hay que procesar

def productor(tarea):
    # coloca la tarea en la cola y avisa por consola
    logger.info(f"[PRODUCTOR] Encolando tarea: {tarea}")
    cola.put(tarea)

def consumidor():
    # aqui se queda escuchando y sacando tareas de la cola
    while True:
        tarea = cola.get()
        try:
            logger.info(f"[CONSUMIDOR] Procesando tarea: {tarea}")
            if tarea == "Generar reporte de pagos":
                time.sleep(1)  # simulamos que se genera el reporte
                enviar_correo_async("administrador_1@gmail.com", "Reporte solicitado", "Adjunto reporte")
        except Exception as e:
            manejar_error("Error procesando tarea", e)
        finally:
            cola.task_done()  # marcamos que la tarea ya se hizo

def iniciar_consumidor():
    # arranca el hilo que va a estar procesando la cola
    hilo = threading.Thread(target=consumidor, daemon=True)
    hilo.start()
    logger.info("[COLA] Consumidor iniciado")
