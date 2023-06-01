from django import template
from django.utils.dateparse import parse_datetime

register = template.Library()

@register.filter(name="cut")
def cut(value, arg):
    return value.replace(arg, "")

@register.filter(name="parse")
def parse(value):
    return parse_datetime(value)