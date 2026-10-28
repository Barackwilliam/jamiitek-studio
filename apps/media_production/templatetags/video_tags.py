"""Show a render's stored (English) progress text in the user's language."""

import re

from django import template
from django.utils.translation import gettext

register = template.Library()

SCENE_PROGRESS = re.compile(r"^Rendering scene (\d+) of (\d+)$")


@register.filter
def progress_text(text):
    match = SCENE_PROGRESS.match(text or "")
    if match:
        return gettext("Rendering scene %(number)s of %(total)s") % {
            "number": match.group(1), "total": match.group(2)}
    return gettext(text) if text else ""
