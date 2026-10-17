import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoBookStore.settings')

app = Celery('DjangoBookStore')
app.config_from_object('django.conf:settings', namespace='CELERY')  # читает все CELERY_* из settings
app.autodiscover_tasks()  # ищет tasks.py в каждом приложении