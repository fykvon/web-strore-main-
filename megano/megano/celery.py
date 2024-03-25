import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'megano.settings')

app = Celery('megano')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
