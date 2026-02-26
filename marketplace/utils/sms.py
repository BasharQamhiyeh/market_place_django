import logging
import secrets

logger = logging.getLogger(__name__)


def send_sms_code(phone: str, purpose: str = "verify") -> str:
    """
    Generate a cryptographically random 6-digit OTP and (in production)
    dispatch it via an SMS gateway.

    TODO: Replace the log statement below with a real SMS gateway call
    (e.g. Twilio, Vonage) before going to production.
    """
    code = str(secrets.randbelow(900000) + 100000)  # 100000 – 999999
    # Development-only: log to console/file instead of sending a real SMS.
    # Remove / replace this line when an SMS gateway is integrated.
    logger.info("[DEV] %s OTP for %s: %s", purpose.upper(), phone, code)
    return code