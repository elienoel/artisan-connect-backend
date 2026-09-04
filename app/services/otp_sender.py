import logging

from app.models.otp import OtpChannel

logger = logging.getLogger(__name__)


def send_otp(channel: OtpChannel, destination: str, code: str) -> None:
    """Delivers an OTP code to the user.

    This is a stand-in until a real SMS provider (Twilio, a local telco
    gateway, ...) or transactional email provider is wired up: it just logs
    the code server-side instead of delivering it, so the rest of the OTP
    flow (generation, expiry, verification) can be built and tested now and
    a real sender dropped in later without touching the calling code.
    """
    logger.info("OTP code for %s (%s): %s", destination, channel.value, code)
