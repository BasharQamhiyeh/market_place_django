from django import template

register = template.Library()

@register.filter
def get_bound_field(form, name):
    try:
        return form[name]
    except Exception:
        return ""

@register.filter
def getitem(form, name):
    """
    Allow template access to form fields dynamically:
    {{ form|getitem:'field_name' }}
    """
    try:
        return form[name]
    except Exception:
        return ""
