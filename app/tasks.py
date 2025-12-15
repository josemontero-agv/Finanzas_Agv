# app/tasks.py
from celery import shared_task
from scripts.etl.etl_sync_threading import run_etl
import logging

logger = logging.getLogger(__name__)

@shared_task(name="run_etl_sync")
def task_run_etl_sync():
    """
    Tarea de Celery que ejecuta la sincronización Odoo -> Supabase.
    Esta tarea es ejecutada por el contenedor 'worker'.
    """
    logger.info("Iniciando tarea ETL Sync desde Celery...")
    try:
        # Ejecuta el script que ya tienes
        run_etl()
        return "Sincronización ETL Completada"
    except Exception as e:
        logger.error(f"Error crítico en ETL: {e}")
        raise e

