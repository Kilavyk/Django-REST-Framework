import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Установка переменной окружения для настроек проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создание экземпляра объекта Celery
app = Celery('config')

# Загрузка настроек из файла Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из файлов tasks.py в приложениях Django
app.autodiscover_tasks()

# Настройка периодических задач для Celery Beat
# app.conf.beat_schedule = {
#     # Проверка неактивных пользователей - каждый день в 2:00 ночи
#     'deactivate-inactive-users-daily': {
#         'task': 'users.tasks.deactivate_inactive_users',
#         'schedule': crontab(hour=2, minute=0),
#     },
#
#     # Дополнительная проверка - каждый понедельник в 3:00 утра
#     'weekly-user-activity-check': {
#         'task': 'users.tasks.check_user_activity',
#         'schedule': crontab(day_of_week=1, hour=3, minute=0),  # 1 = понедельник
#     },
# }

app.conf.timezone = settings.TIME_ZONE
