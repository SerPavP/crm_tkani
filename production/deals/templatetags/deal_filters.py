from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def format_price(value):
    """
    Форматирует цену с разделителями тысяч
    Пример: 183227.49 -> 183 227,49
    """
    if value is None:
        return "0,00"
    
    try:
        # Преобразуем в число
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        else:
            value = float(value)
        
        # Форматируем с двумя знаками после запятой
        formatted = f"{value:.2f}"
        
        # Разделяем на целую и дробную части
        if '.' in formatted:
            integer_part, decimal_part = formatted.split('.')
        else:
            integer_part = formatted
            decimal_part = '00'
        
        # Добавляем разделители тысяч в целую часть
        if len(integer_part) > 3:
            # Разбиваем на группы по 3 цифры справа налево
            groups = []
            for i in range(len(integer_part), 0, -3):
                start = max(0, i - 3)
                groups.insert(0, integer_part[start:i])
            integer_part = ' '.join(groups)
        
        # Возвращаем результат с запятой в качестве десятичного разделителя
        return f"{integer_part},{decimal_part}"
    
    except (ValueError, TypeError):
        return "0,00" 