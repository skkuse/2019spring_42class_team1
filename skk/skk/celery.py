import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skk.settings')
app = Celery('skk')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(
    BROKER_URL=settings.CELERY_BROKER_URL,
    CELERY_TASK_SERIALIZER=settings.CELERY_TASK_SERIALIZER,
    CELERY_ACCEPT_CONTENT=settings.CELERY_ACCEPT_CONTENT,
    CELERY_RESULT_SERIALIZER=settings.CELERY_RESULT_SERIALIZER,
    CELERY_TIMEZONE=settings.CELERY_TIMEZONE,
    CELERY_ENABLE_UTC=settings.CELERY_ENABLE_UTC,
)
