"""
Celery Configuration for SwasthyaAI Regulator
Enables async processing of large document submissions
"""

from celery import Celery
import os
from datetime import timedelta

# Redis broker configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery('swasthya_regulator')

# Celery configuration
celery_app.conf.update(
    # Broker settings
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Results backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_compression='gzip',
    
    # Task routing
    task_routes={
        'celery_tasks.task_extract_document': {'queue': 'processing'},
        'celery_tasks.task_anonymize_text': {'queue': 'processing'},
        'celery_tasks.task_summarize_text': {'queue': 'processing'},
        'celery_tasks.task_validate_compliance': {'queue': 'processing'},
        'celery_tasks.task_process_submission_pipeline': {'queue': 'processing'},
    },
    
    # Beat schedule (if using periodic tasks)
    beat_schedule={
        'cleanup-old-results': {
            'task': 'celery_tasks.task_cleanup_results',
            'schedule': timedelta(hours=6),
        },
    }
)

# Task autodiscovery
celery_app.autodiscover_tasks(['celery_tasks'])

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
