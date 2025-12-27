from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def format_unit(value, material_or_unit):
    """
    Formata um valor (assumido em base mm) para a unidade de exibição.
    Uso: {{ valor | format_unit:material_obj }} ou {{ valor | format_unit:'mt' }}
    """
    if value is None:
        return ""
    
    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return value

    # Se passou um objeto Material (ou similar que tenha is_unidade_medida)
    if hasattr(material_or_unit, 'get_valor_display'):
        return f"{material_or_unit.get_valor_display(val_float):.2f}"
    
    # Se passou string direta (ex: 'mt')
    unit_str = str(material_or_unit).lower().strip()
    if unit_str in ['mt', 'm', 'mts', 'metro', 'metros']:
        return f"{val_float / 1000.0:.2f}"
    elif unit_str in ['cm', 'centimetro']:
        return f"{val_float / 10.0:.2f}"
        
    return f"{val_float:.2f}"
