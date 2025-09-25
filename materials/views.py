from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, Lesson, Subscription
from materials.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsOwner
from materials.tasks import send_course_update_notification

from .paginators import CoursePagination, LessonPagination


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с курсами.

    list:
    Получить список всех курсов. Требуется аутентификация.

    create:
    Создать новый курс. Требуется аутентификация, модераторы не могут создавать курсы.

    retrieve:
    Получить детальную информацию о курсе. Требуется аутентификация.

    update:
    Обновить информацию о курсе. Требуется аутентификация и права модератора/владельца/администратора.

    partial_update:
    Частично обновить информацию о курсе. Требуется аутентификация и права модератора/владельца/администратора.

    destroy:
    Удалить курс. Требуется аутентификация и права модератора/владельца/администратора.
    """

    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    pagination_class = CoursePagination

    def get_permissions(self):
        # Для генерации схемы пропускаем проверку прав
        if getattr(self, "swagger_fake_view", False):
            return []

        if self.action == "create":
            self.permission_classes = [IsAuthenticated, ~IsModerator]
        elif self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = [
                IsAuthenticated,
                IsModerator | IsOwner | IsAdminUser,
            ]
        elif self.action in ["retrieve", "list"]:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        # Для генерации схемы возвращаем пустой queryset
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

        if not self.request.user.is_staff and not IsModerator().has_permission(
            self.request, self
        ):
            return self.queryset.filter(owner=self.request.user)
        return self.queryset

    def update(self, request, *args, **kwargs):
        """Переопределяем update для отправки уведомлений"""
        response = super().update(request, *args, **kwargs)

        # Отправляем асинхронное уведомление об обновлении курса
        course_id = self.get_object().id
        send_course_update_notification.delay(course_id)
        return response


class LessonCreateAPIView(generics.CreateAPIView):
    """
    Создать новый урок.

    Требуется аутентификация. Модераторы не могут создавать уроки.
    """

    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, ~IsModerator]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonListAPIView(generics.ListAPIView):
    """
    Получить список всех уроков.

    Требуется аутентификация. Обычные пользователи видят только свои уроки,
    модераторы и администраторы видят все уроки.
    """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LessonPagination

    def get_queryset(self):
        # Для генерации схемы возвращаем пустой queryset
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        if not self.request.user.is_staff and not IsModerator().has_permission(
            self.request, self
        ):
            return Lesson.objects.filter(owner=self.request.user)
        return Lesson.objects.all()


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """
    Получить детальную информацию об уроке по ID.

    Требуется аутентификация и права модератора/владельца/администратора.
    """

    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsModerator | IsOwner | IsAdminUser]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """
    Обновить информацию об уроке.

    Требуется аутентификация и права модератора/владельца/администратора.
    """

    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsModerator | IsOwner | IsAdminUser]


class LessonDestroyAPIView(generics.DestroyAPIView):
    """
    Удалить урок.

    Требуется аутентификация и права владельца/администратора.
    """

    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsAdminUser]


class SubscriptionAPIView(APIView):
    """
    Добавить или удалить подписку на курс.

    Требуется аутентификация.

    Параметры запроса:
    - course_id: ID курса для подписки/отписки

    Возвращает:
    - message: Сообщение о результате операции
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            subscription.delete()
            message = "Подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course)
            message = "Подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)
