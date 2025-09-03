import logging

logger = logging.getLogger(__name__)

def manejar_error(mensaje, exc=None):
    logger.error(f"[ERROR] {mensaje}")
    if exc:
        logger.exception(exc)
