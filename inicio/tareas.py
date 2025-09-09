import logging
import threading
import time
from .errores import manejar_error

logger = logging.getLogger(__name__)

def enviar_correo_async(destinatario, asunto, cuerpo):
    def _enviar():
        try:
            logger.info(f"[HILO] Enviando correo a {destinatario} con asunto: {asunto}")
            time.sleep(2)
            logger.info("[HILO] Correo enviado correctamente")
        except Exception as e:
            manejar_error("Error enviando correo", e)
    threading.Thread(target=_enviar, daemon=True).start()
