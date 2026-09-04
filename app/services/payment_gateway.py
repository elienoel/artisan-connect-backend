import uuid
from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    reference: str


def charge(amount: float, currency: str, description: str) -> PaymentResult:
    """Stand-in for a real payment provider (a Mobile Money aggregator such
    as CinetPay/PayDunya, or Stripe for card payments). Always succeeds
    instantly so the subscription/boost flow can be built and tested now —
    swap this for a real gateway call later without touching the callers,
    which only look at PaymentResult.success/reference.
    """
    return PaymentResult(success=True, reference=f"SIMULATED-{uuid.uuid4()}")
