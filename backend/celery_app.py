"""
Celery App Configuration - Production Ready
Este módulo configura Celery de forma correcta para uso con Flask y Docker.
"""

from celery import Celery
from app import create_app, db
import os

# Crear la aplicación Flask
flask_app = create_app()

# Configurar Celery con la configuración de Flask
celery = Celery(
    'backorder_pcm',
    broker=flask_app.config['CELERY_BROKER_URL'],
    backend=flask_app.config['CELERY_RESULT_BACKEND']
)

# Configuración adicional de Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos máximo por tarea
    task_soft_time_limit=25 * 60,  # 25 minutos soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configurar Beat Schedule (tareas periódicas)
celery.conf.beat_schedule = {
    'sync-all-erps-every-hour': {
        'task': 'app.services.sync_service.sync_all_erps',
        'schedule': 3600.0,  # cada hora
    },
}


class ContextTask(celery.Task):
    """
    Tarea base que asegura el contexto de Flask en todas las tareas.
    Esto permite que las tareas accedan a db.session y otros recursos de Flask.
    """
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


# Establecer la tarea base para todas las tareas
celery.Task = ContextTask

# Autodiscover tasks en los módulos especificados
celery.autodiscover_tasks(['app.services'], force=True)

# También importar explícitamente las tareas principales
try:
    from app.services.sync_service import sync_all_erps
    print(f"✓ Task importada: {sync_all_erps.name}")
except Exception as e:
    print(f"⚠ Error importando tasks: {e}")


if __name__ == '__main__':
    # Esto permite ejecutar celery directamente
    celery.start()
