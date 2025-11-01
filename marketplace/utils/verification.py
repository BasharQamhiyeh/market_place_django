from django.utils import timezone
from datetime import timedelta

CODE_EXPIRY_MINUTES = 10

def send_code(request, phone, key_prefix, purpose, send_func):
    """
    Generate + send a code, then store it in session.
    """
    code = send_func(phone, purpose)
    request.session[f"{key_prefix}_code"] = code
    request.session[f"{key_prefix}_sent_at"] = timezone.now().isoformat()

    return code


def verify_session_code(request, key_prefix, entered_code):
    """
    Verify the code stored in session for the given purpose.
    """
    stored_code = request.session.get(f"{key_prefix}_code")
    sent_at = request.session.get(f"{key_prefix}_sent_at")

    if not stored_code or not sent_at:
        return False

    sent_time = timezone.datetime.fromisoformat(sent_at)
    if timezone.now() - sent_time > timedelta(minutes=CODE_EXPIRY_MINUTES):
        return False

    return entered_code.strip() == stored_code.strip()
