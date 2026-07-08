from celery import Celery, Task
from flask import Flask

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_config = app.config["CELERY"]
    celery_app.config_from_object(celery_config)
    # config_from_object ya propaga 'beat_schedule' (verificado: Celery acepta dicts con
    # claves lowercase estilo Celery 4+), pero lo reafirmamos explícitamente para que
    # `celery -A celery_worker.celery beat` siempre encuentre la tarea programada aunque
    # cambie el mecanismo interno de config_from_object en futuras versiones de Celery.
    if celery_config.get('beat_schedule'):
        celery_app.conf.beat_schedule = celery_config['beat_schedule']
    celery_app.Task = FlaskTask
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

