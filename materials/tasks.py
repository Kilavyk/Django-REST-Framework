from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from materials.models import Course, Subscription


@shared_task
def send_course_update_notification(course_id):
    """
    Асинхронная задача для отправки уведомлений об обновлении курса
    """
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(course=course)

        if not subscriptions.exists():
            return f"Нет подписчиков на курс {course.title}"

        subject = f'Обновление курса: {course.title}'

        for subscription in subscriptions:
            user = subscription.user
            context = {
                'course_title': course.title,
                'user_name': user.first_name or user.email,
                'course_description': course.description,
            }

            # HTML версия письма
            html_message = render_to_string('materials/course_update_email.html', context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        return f"Отправленных уведомлений {subscriptions.count()} для курса {course.title}"

    except Course.DoesNotExist:
        return f"Курс с идентификатором {course_id} не существует"
    except Exception as e:
        return f"Ошибка при отправке уведомлений: {str(e)}"