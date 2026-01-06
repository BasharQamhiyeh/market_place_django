# your_app/templatetags/timeago_ar.py
from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def timeago_ar(value):
    """
    Arabic 'time ago' like your JS rules.
    Usage: {{ some_datetime|timeago_ar }}
    """
    if not value:
        return ""

    now = timezone.now()

    # make both aware (or both naive) safely
    if timezone.is_aware(now) and timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    elif timezone.is_naive(now) and timezone.is_aware(value):
        value = timezone.make_naive(value, timezone.get_current_timezone())

    diff = now - value
    diff_seconds = int(diff.total_seconds())
    if diff_seconds < 0:
        diff_seconds = 0

    minutes = diff_seconds // 60
    hours = diff_seconds // 3600
    days = diff_seconds // 86400
    weeks = days // 7
    months = days // 30

    if minutes < 1:
        return "الآن"
    if minutes == 1:
        return "منذ دقيقة"
    if minutes == 2:
        return "منذ دقيقتين"
    if minutes < 60:
        return f"منذ {minutes} دقائق"

    if hours == 1:
        return "منذ ساعة"
    if hours == 2:
        return "منذ ساعتين"
    if hours < 24:
        return f"منذ {hours} ساعات"

    if days == 1:
        return "منذ يوم"
    if days == 2:
        return "منذ يومين"
    if days < 7:
        return f"منذ {days} أيام"

    if weeks == 1:
        return "منذ أسبوع"
    if weeks == 2:
        return "منذ أسبوعين"
    if weeks < 4:
        return f"منذ {weeks} أسابيع"

    if months == 1:
        return "منذ شهر"
    if months == 2:
        return "منذ شهرين"
    return f"منذ {months} أشهر"
