import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def tojson(value):
    """Render a Python value as raw, safe JSON.

    Used to embed a stored GeoJSON dict into a
    `<script type="application/json" id="...">` block or a data attribute.
    Values are validated numeric geometries, so the raw output is safe.
    """
    return mark_safe(json.dumps(value))