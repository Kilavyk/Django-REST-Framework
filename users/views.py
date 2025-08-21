from rest_framework import generics
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, BasePermission

from users.models import Payment, User
from users.permissions import IsOwnerOrStaff
from users.serializers import PaymentSerializer, UserSerializers


class PaymentListAPIView(generics.ListAPIView):
    """
    Получить список платежей с возможностью фильтрации и сортировки.

    Доступные фильтры:
    - paid_course: ID курса
    - paid_lesson: ID урока
    - payment_method: Способ оплаты (cash/transfer)

    Доступная сортировка:
    - payment_date: Дата оплаты
    - -payment_date: Дата оплаты в обратном порядке
    """
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['paid_course', 'paid_lesson', 'payment_method']
    ordering_fields = ['payment_date']


class UserCreateAPIView(CreateAPIView):
    """
    Регистрация нового пользователя.

    Не требует аутентификации.
    """
    serializer_class = UserSerializers
    queryset = User.objects.all()
    permission_classes = []

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.save()


class UserRetrieveAPIView(RetrieveAPIView):
    """
    Получить информацию о пользователе по ID.

    Требуется аутентификация и права владельца/администратора.
    """
    serializer_class = UserSerializers
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]


class UserUpdateAPIView(UpdateAPIView):
    """
    Обновить информацию о пользователе.

    Требуется аутентификация и права владельца/администратора.
    """
    serializer_class = UserSerializers
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]


class UserDestroyAPIView(DestroyAPIView):
    """
    Удалить пользователя.

    Требуется аутентификация и права владельца/администратора.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]