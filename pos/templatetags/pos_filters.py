from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def format_currency(value):
    """
    Formatea un número como moneda con separadores de miles
    Ejemplo: 50000 -> 50,000
    """
    if value is None:
        return "0"
    
    try:
        # Convertir a entero si es posible
        if isinstance(value, str):
            # Remover puntos y comas existentes
            value = value.replace('.', '').replace(',', '')
            value = int(float(value))
        else:
            value = int(value)
        
        # Formatear con separadores de miles
        formatted = f"{value:,}"
        return mark_safe(formatted)
    except (ValueError, TypeError):
        return str(value)

@register.filter
def currency(value):
    """
    Formatea un número como moneda con símbolo $ y separadores de miles
    Ejemplo: 50000 -> $50,000
    """
    if value is None:
        return "$0"
    
    try:
        # Convertir a entero si es posible
        if isinstance(value, str):
            # Remover puntos y comas existentes
            value = value.replace('.', '').replace(',', '')
            value = int(float(value))
        else:
            value = int(value)
        
        # Formatear con separadores de miles y símbolo $
        formatted = f"${value:,}"
        return mark_safe(formatted)
    except (ValueError, TypeError):
        return f"${value}"

