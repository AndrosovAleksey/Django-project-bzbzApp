from django import template

register = template.Library()

@register.filter
def truncate_token(value, length=10):
    """
    Обрезает строку до указанной длины и добавляет многоточие.
    Пример: 'abcdefghijklmno' -> 'abcdefghij...'
    """
    if len(value) > length:
        return value[:length] + '...'
    return value