# marketplace/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Match any opening HTML/SVG tag that can carry scripts or external resources
HTML_TAG_PATTERN = re.compile(
    r'<\s*(script|iframe|object|embed|form|img|a|svg|style|link|base|meta'
    r'|input|button|select|textarea|details|dialog)\b',
    re.IGNORECASE,
)

# Inline event handlers (onclick=, onload=, onerror=, …)
EVENT_HANDLER_PATTERN = re.compile(r'\bon\w+\s*=', re.IGNORECASE)

# javascript: / vbscript: URI schemes (href="javascript:…", src="javascript:…")
DANGEROUS_SCHEME_PATTERN = re.compile(r'\b(javascript|vbscript|data)\s*:', re.IGNORECASE)

# Plain URLs
URL_PATTERN = re.compile(r'(https?://|www\.)', re.IGNORECASE)


def validate_no_links_or_html(value):
    """
    Reject values that contain URLs, HTML tags, inline event handlers, or
    dangerous URI schemes that could be used for XSS or phishing.
    """
    if not value:
        return value

    text = str(value)

    if (
        URL_PATTERN.search(text)
        or HTML_TAG_PATTERN.search(text)
        or EVENT_HANDLER_PATTERN.search(text)
        or DANGEROUS_SCHEME_PATTERN.search(text)
    ):
        raise ValidationError(
            _("Links or HTML are not allowed in this field.")
        )

    return value
