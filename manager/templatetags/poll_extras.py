from django import template
from django.utils.dateparse import parse_datetime
import datetime
register = template.Library()


@register.filter(name="cut")
def cut(value, arg):
    return value.replace(arg, "")


@register.filter(name="parse")
def parse(value):
    return parse_datetime(value)


@register.filter
def plus_days(value, days):
    return value + datetime.timedelta(days=days)
