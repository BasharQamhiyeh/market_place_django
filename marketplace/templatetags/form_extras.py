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


@register.filter
def getitem(obj, key):
    """Allow template access: form|getitem:'field_name' """
    return obj.get(key)