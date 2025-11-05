from django import template

register = template.Library()

@register.filter
def instanceof(obj, model_name):
    """
    Checks if the given object is an instance of the specified model name.
    Usage in template: {% if my_object|instanceof:"RideRequest" %}
    """
    return obj.__class__.__name__ == model_name

@register.filter
def shorten_address(address):
    """
    Returns the first part of an address (text before the first comma).
    Usage: {{ ride.pickup_location|shorten_address }}
    """
    if not address:
        return ''
    # Split by comma and return the first part, strip whitespace
    return address.split(',')[0].strip()