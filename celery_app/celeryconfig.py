from celery.schedules import crontab
from dotenv import load_dotenv

from config import REDIS_URL

load_dotenv()

beat_schedule = {
    'data-collection': {
        'task': 'celery_app.tasks.daily_task',
        'schedule': crontab(hour=5, minute=30),
    }
}

broker_url = REDIS_URL
timezone = 'UTC'
task_track_started = True



