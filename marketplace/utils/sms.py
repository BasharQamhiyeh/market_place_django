import random

def send_sms_code(phone: str, purpose: str = "verify") -> str:
    """Simulate sending SMS and return a random 6-digit code."""
    code = str("000000")
    print(f"[DEV MODE] {purpose.upper()} code for {phone}: {code}")
    return code
