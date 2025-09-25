from rest_framework import generics, status
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.urls import reverse

from users.models import Payment, User
from users.permissions import IsOwnerOrStaff
from users.serializers import PaymentSerializer, UserSerializers
from materials.services import (
    create_stripe_product,
    create_stripe_price,
    create_stripe_checkout_session,
    get_stripe_session_status,
)
from materials.models import Course, Lesson


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
    filterset_fields = ["paid_course", "paid_lesson", "payment_method"]
    ordering_fields = ["payment_date"]


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


# Stripe
class CreatePaymentAPIView(APIView):
    """Создание платежа и сессии оплаты в Stripe"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        course_id = request.data.get("course_id")
        lesson_id = request.data.get("lesson_id")

        if not course_id and not lesson_id:
            return Response(
                {"error": "Необходимо указать course_id или lesson_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Получаем объект курса или урока
        if course_id:
            product = get_object_or_404(Course, id=course_id)
            product_type = "course"
        else:
            product = get_object_or_404(Lesson, id=lesson_id)
            product_type = "lesson"

        # Создаем продукт в Stripe
        stripe_product = create_stripe_product(
            name=product.title, description=product.description
        )

        if not stripe_product:
            return Response(
                {"error": "Ошибка при создании продукта в Stripe"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Предположим, что цена уже хранится в продукте
        if product_type == "course":
            amount = 15000
        else:
            amount = 2000

        stripe_price = create_stripe_price(product_id=stripe_product.id, amount=amount)

        if not stripe_price:
            return Response(
                {"error": "Ошибка при создании цены в Stripe"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Создаем сессию оплаты
        success_url = request.build_absolute_uri(reverse("payment-success"))
        cancel_url = request.build_absolute_uri(reverse("payment-cancel"))

        stripe_session = create_stripe_checkout_session(
            price_id=stripe_price.id, success_url=success_url, cancel_url=cancel_url
        )

        if not stripe_session:
            return Response(
                {"error": "Ошибка при создании сессии оплаты"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Создаем запись о платеже в нашей системе
        payment = Payment.objects.create(
            user=user,
            paid_course=product if product_type == "course" else None,
            paid_lesson=product if product_type == "lesson" else None,
            amount=amount,
            payment_method="transfer",
            stripe_product_id=stripe_product.id,
            stripe_price_id=stripe_price.id,
            stripe_session_id=stripe_session.id,
            stripe_payment_url=stripe_session.url,
            stripe_payment_status="pending",
        )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentStatusAPIView(APIView):
    """Проверка статуса платежа"""

    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)

        # Обновляем статус из Stripe
        session_status = get_stripe_session_status(payment.stripe_session_id)

        if session_status:
            payment.stripe_payment_status = session_status.payment_status
            payment.save()

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)


class PaymentSuccessAPIView(APIView):
    """Обработка успешной оплаты"""

    def get(self, request):
        session_id = request.GET.get("session_id")
        if session_id:
            payment = Payment.objects.filter(stripe_session_id=session_id).first()
            if payment:
                payment.stripe_payment_status = "paid"
                payment.save()

        return Response({"message": "Оплата прошла успешно!"})


class PaymentCancelAPIView(APIView):
    """Обработка отмены оплаты"""

    def get(self, request):
        return Response({"message": "Оплата отменена. Вы можете попробовать снова."})
