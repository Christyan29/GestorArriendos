import logging
import threading
import time
from .errores import manejar_error

logger = logging.getLogger(__name__)

def enviar_correo_async(destinatario, asunto, cuerpo):
    # esta funcion simula mandar un correo pero sin frenar el resto del sistema
    def _enviar():
        try:
            logger.info(f"[HILO] Enviando correo a {destinatario} con asunto: {asunto}")
            time.sleep(2)  # tiempo que tarda en enviar el correo
            logger.info("[HILO] Correo enviado correctamente")
        except Exception as e:
            manejar_error("Error enviando correo", e)

    # se ejecuta el hilo para que corra en segundo plano
    threading.Thread(target=_enviar, daemon=True).start()
