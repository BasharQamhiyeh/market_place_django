# marketplace/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Very simple patterns; we can refine later if needed
URL_PATTERN = re.compile(r'(https?://|www\.)', re.IGNORECASE)
HTML_PATTERN = re.compile(r'<\s*(script|iframe|object|embed|form|img|a)\b', re.IGNORECASE)

def validate_no_links_or_html(value):
    """
    Reject values that contain obvious URLs or HTML tags that could be used
    for XSS or unwanted links.
    """
    if not value:
        return value

    text = str(value)

    if URL_PATTERN.search(text) or HTML_PATTERN.search(text):
        raise ValidationError(
            _("Links or HTML are not allowed in this field.")
        )

    return value
