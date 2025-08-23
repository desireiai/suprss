# core/celery_app.py
from celery import Celery
import os
import logging

logger = logging.getLogger(__name__)

# Configuration Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Créer l'instance Celery
celery_app = Celery(
    'suprss',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['core.tasks']  # Inclure les tâches
)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configuration Beat (scheduler)
celery_app.conf.beat_schedule = {
    'update-rss-feeds': {
        'task': 'core.tasks.update_all_rss_feeds',
        'schedule': 3600.0,  # Toutes les heures
    },
    'cleanup-old-articles': {
        'task': 'core.tasks.cleanup_old_articles',
        'schedule': 86400.0,  # Une fois par jour
    },
    'generate-statistics': {
        'task': 'core.tasks.generate_daily_statistics',
        'schedule': 86400.0,  # Une fois par jour
    },
}

if __name__ == '__main__':
    celery_app.start()