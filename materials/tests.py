from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course, Lesson, Subscription
from users.models import User


class LessonCRUDTestCase(APITestCase):
    def setUp(self):
        # Создаем тестовых пользователей
        self.admin = User.objects.create(
            email='admin@test.com',
            is_staff=True,
            is_superuser=True
        )
        self.admin.set_password('test')
        self.admin.save()

        self.moderator = User.objects.create(
            email='moderator@test.com'
        )
        self.moderator.groups.create(name='moderators')
        self.moderator.set_password('test')
        self.moderator.save()

        self.user = User.objects.create(
            email='user@test.com'
        )
        self.user.set_password('test')
        self.user.save()

        # тестовый курс
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

        # тестовый урок
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            description='Test Lesson Description',
            course=self.course,
            video_link='https://www.youtube.com/watch?v=test',
            owner=self.user
        )

    def test_lesson_create_admin(self):
        """Тест создания урока администратором"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'title': 'New Lesson by Admin',
            'description': 'New Description',
            'course': self.course.id,
            'video_link': 'https://www.youtube.com/watch?v=new'
        }
        response = self.client.post(
            reverse('materials:lesson-create'),
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_lesson_create_moderator_denied(self):
        """Тест запрета создания урока модератором"""
        self.client.force_authenticate(user=self.moderator)
        data = {
            'title': 'New Lesson by Moderator',
            'description': 'New Description',
            'course': self.course.id,
            'video_link': 'https://www.youtube.com/watch?v=new'
        }
        response = self.client.post(
            reverse('materials:lesson-create'),
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_lesson_list(self):
        """Тест получения списка уроков"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('materials:lesson-list')
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(response.data['results']), 1)
        # Используем 'results' из-за пагинации

    def test_lesson_update_owner(self):
        """Тест обновления урока владельцем"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Updated Lesson',
            'video_link': 'https://www.youtube.com/watch?v=updated'
        }
        response = self.client.patch(
            reverse('materials:lesson-update', kwargs={'pk': self.lesson.id}),
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.lesson.refresh_from_db()
        self.assertEqual(
            self.lesson.title,
            'Updated Lesson'
        )

    def test_lesson_delete_owner(self):
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse('materials:lesson-delete', kwargs={'pk': self.lesson.id})
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(
            Lesson.objects.count(),
            0
        )

    def test_lesson_video_link_validation(self):
        """Тест валидации ссылки на видео"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Invalid Video Link',
            'description': 'Test',
            'course': self.course.id,
            'video_link': 'https://vimeo.com/test'
        }
        response = self.client.post(
            reverse('materials:lesson-create'),
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertIn(
            'Разрешены только ссылки на youtube.com',
            str(response.data)
        )


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            email='user@test.com'
        )
        self.user.set_password('test')
        self.user.save()

        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

    def test_subscribe_unsubscribe(self):
        """Тест подписки и отписки от курса"""
        self.client.force_authenticate(user=self.user)

        # Подписываемся
        response = self.client.post(
            reverse('materials:subscription'),
            data={'course_id': self.course.id}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data['message'],
            'Подписка добавлена'
        )
        self.assertTrue(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )

        # Отписываемся
        response = self.client.post(
            reverse('materials:subscription'),
            data={'course_id': self.course.id}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data['message'],
            'Подписка удалена'
        )
        self.assertFalse(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_is_subscribed_field(self):
        """Тест поля is_subscribed в сериализаторе курса"""
        # Создаем подписку
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('materials:course-detail', kwargs={'pk': self.course.id})
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(
            response.data['is_subscribed']
        )
