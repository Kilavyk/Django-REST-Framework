from django.urls import path
from users.views import PaymentListAPIView

urlpatterns = [
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
]
