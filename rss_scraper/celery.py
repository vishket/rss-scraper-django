import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rss_scraper.settings")

app = Celery("rss_scraper")
app.config_from_object("django.conf.settings", namespace="CELERY")
app.autodiscover_tasks()
