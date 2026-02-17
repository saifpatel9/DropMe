from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def before_comma(value):
    if value is None:
        return ""
    text = str(value)
    return text.split(",", 1)[0].strip()
