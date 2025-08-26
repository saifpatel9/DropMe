from django import template

register = template.Library()

@register.filter
def instanceof(obj, model_name):
    """
    Checks if the given object is an instance of the specified model name.
    Usage in template: {% if my_object|instanceof:"RideRequest" %}
    """
    return obj.__class__.__name__ == model_name