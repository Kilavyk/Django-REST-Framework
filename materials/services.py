import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name, description=None):
    """Создание продукта в Stripe"""
    try:
        product = stripe.Product.create(
            name=name,
            description=description,
        )
        return product
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании продукта: {e}")
        return None


def create_stripe_price(product_id, amount, currency="rub"):
    """Создание цены в Stripe"""
    try:
        # Конвертируем в копейки (центы)
        unit_amount = int(amount * 100)

        price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
        )
        return price
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании цены: {e}")
        return None


def create_stripe_checkout_session(price_id, success_url, cancel_url):
    """Создание сессии для оплаты в Stripe"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании сессии: {e}")
        return None


def get_stripe_session_status(session_id):
    """Получение статуса сессии оплаты"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except stripe.error.StripeError as e:
        print(f"Ошибка при получении статуса сессии: {e}")
        return None
