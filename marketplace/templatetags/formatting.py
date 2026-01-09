from django import template

register = template.Library()

@register.filter
def compact_ar_k(value):
    """
    1200 -> (1.2, True)
    999  -> (999, False)
    """
    try:
        v = int(value or 0)
    except (TypeError, ValueError):
        v = 0

    if v >= 1000:
        num = round(v / 1000, 1)
        # remove trailing .0
        if num.is_integer():
            num = int(num)
        return {"num": num, "is_k": True}
    return {"num": v, "is_k": False}
