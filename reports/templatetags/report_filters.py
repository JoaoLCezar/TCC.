from django import template
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplica dois valores"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def subtract(value, arg):
    """Subtrai dois valores"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter(name="currency_br")
def currency_br(value):
    """Formata um número/Decimal como moeda BRL: R$ 1.234,56"""
    try:
        number = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, InvalidOperation):
        return "R$ 0,00"

    sign = "-" if number < 0 else ""
    number = abs(number)
    inteiro, frac = divmod(int(number * 100), 100)
    inteiro_str = f"{inteiro:,}".replace(",", ".")
    frac_str = f"{frac:02d}"
    return f"R$ {sign}{inteiro_str},{frac_str}"

@register.filter(name="has_group")
def has_group(user, group_name: str):
    """Retorna True se o usuário pertence ao grupo informado."""
    try:
        # Superuser or staff should be treated as having all groups for UI purposes
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False
