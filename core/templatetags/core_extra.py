from datetime import datetime
from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@register.filter
def short_since(value):
    if not value or not isinstance(value, datetime):
        return value

    now = timezone.now()
    delta = now - value

    if delta < timedelta(seconds=60):
        return f"{int(delta.seconds)}s"

    if delta < timedelta(minutes=60):
        return f"{delta.seconds // 60}m"

    if delta < timedelta(hours=24):
        return f"{delta.seconds // (60 * 60)}h"

    if delta < timedelta(days=365):
        return f"{value.day} {MONTHS[value.month - 1]}"

    return value.strftime("%Y-%m-%d")
