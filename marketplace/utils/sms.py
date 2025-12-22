import random

def send_sms_code(phone: str, purpose: str = "verify") -> str:
    """Simulate sending SMS and return a random 6-digit code."""
    code = str("0000")
    print(f"[DEV MODE] {purpose.upper()} code for {phone}: {code}")
    return code


def send_verification_code(phone):
    code = str(random.randint(100000, 999999))
    # TODO: integrate your SMS gateway here
    print(f"✅ Sending code {code} to {phone}")
    return code