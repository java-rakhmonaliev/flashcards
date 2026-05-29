from django import template
import math

register = template.Library()

@register.filter
def progress_offset(percent):
    circumference = 2 * math.pi * 22  # 138.23
    return round(circumference * (1 - (percent or 0) / 100), 2)