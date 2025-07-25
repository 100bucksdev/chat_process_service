from celery import Celery

celery_app = Celery('save_lot_data')
celery_app.config_from_object('celery_app.celeryconfig')

celery_app.autodiscover_tasks(['celery_app'])

import celery_app.tasks