from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """Умножает значение на аргумент."""
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def div(value, arg):
    """Делит значение на аргумент."""
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return '' 