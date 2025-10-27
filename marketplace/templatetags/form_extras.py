from django import template

register = template.Library()

@register.filter
def get_bound_field(form, name):
    """
    Safely return a bound field inside the form by dynamic name.
    If not found — return empty string instead of crashing.
    """
    try:
        return form[name]
    except Exception:
        return ""
