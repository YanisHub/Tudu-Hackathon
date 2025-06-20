import uuid
from decimal import Decimal
from django.conf import settings


try:
    import stripe
except Exception:  # pragma: no cover - stripe may not be installed in tests
    stripe = None

if stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class DummyIntent:
    """Fallback intent object when Stripe keys are not configured."""
    def __init__(self):
        self.id = f"pi_{uuid.uuid4().hex}"
        self.client_secret = "dummy"


def create_payment_intent(amount, metadata=None):
    """Create a Stripe PaymentIntent or return a dummy object in tests."""
    if not stripe or not settings.STRIPE_SECRET_KEY:
        return DummyIntent()

    intent = stripe.PaymentIntent.create(
        amount=int(Decimal(amount) * 100),
        currency="usd",
        payment_method_types=["card"],
        capture_method="manual",
        metadata=metadata or {},
    )
    return intent


def capture_payment_intent(intent_id):
    if stripe and settings.STRIPE_SECRET_KEY:
        stripe.PaymentIntent.capture(intent_id)


def refund_payment_intent(intent_id):
    if stripe and settings.STRIPE_SECRET_KEY:
        stripe.Refund.create(payment_intent=intent_id)


def construct_event(payload, sig_header):
    if not stripe or not settings.STRIPE_WEBHOOK_SECRET:
        return None
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
