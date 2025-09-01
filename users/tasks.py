from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def deactivate_inactive_users():
    """
    Задача для деактивации пользователей, которые не заходили более месяца
    """
    try:
        # Вычисляем дату, которая была 30 дней назад
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Находим пользователей, которые не заходили более месяца и еще активны
        inactive_users = User.objects.filter(
            last_login__lt=thirty_days_ago,
            is_active=True
        )

        # Деактивируем пользователей
        count = inactive_users.count()
        inactive_users.update(is_active=False)

        return f"Деактивировано {count} неактивных пользователей"

    except Exception as e:
        return f"Ошибка при деактивации неактивных пользователей: {str(e)}"


@shared_task
def check_user_activity():
    """
    Общая задача для проверки активности пользователей
    """
    return deactivate_inactive_users()
