import secrets
from datetime import timedelta

from django.utils import timezone

CODE_EXPIRY_MINUTES = 10


def send_code(request, phone, key_prefix, purpose, send_func):
    """Generate + send a code, then store it in session."""
    code = send_func(phone, purpose)
    request.session[f"{key_prefix}_code"] = code
    request.session[f"{key_prefix}_sent_at"] = timezone.now().isoformat()
    return code


def verify_session_code(request, key_prefix, entered_code):
    """
    Verify the code stored in session for the given purpose.

    Uses secrets.compare_digest to prevent timing-oracle attacks.
    Clears the code from session on successful verification to prevent
    replay attacks.
    """
    stored_code = request.session.get(f"{key_prefix}_code")
    sent_at = request.session.get(f"{key_prefix}_sent_at")

    if not stored_code or not sent_at:
        return False

    sent_time = timezone.datetime.fromisoformat(sent_at)
    if timezone.now() - sent_time > timedelta(minutes=CODE_EXPIRY_MINUTES):
        # Expired — remove stale values
        request.session.pop(f"{key_prefix}_code", None)
        request.session.pop(f"{key_prefix}_sent_at", None)
        return False

    # Constant-time comparison to prevent timing attacks
    match = secrets.compare_digest(
        entered_code.strip(),
        stored_code.strip(),
    )

    if match:
        # Consume the code so it cannot be reused
        request.session.pop(f"{key_prefix}_code", None)
        request.session.pop(f"{key_prefix}_sent_at", None)

    return match
