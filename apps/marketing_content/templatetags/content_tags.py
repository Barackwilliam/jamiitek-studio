"""Template helpers for showing claim-check flags in the user's language."""

import re

from django import template
from django.utils.translation import gettext, pgettext

register = template.Library()

FIELD_LABELS = {
    "title": lambda: pgettext("script field", "title"),
    "headline": lambda: pgettext("script field", "headline"),
    "caption": lambda: pgettext("script field", "caption"),
    "call_to_action": lambda: pgettext("script field", "call to action"),
    "hashtags": lambda: pgettext("script field", "hashtags"),
    "angle": lambda: pgettext("script field", "angle"),
    "key_message": lambda: pgettext("script field", "key message"),
    "voiceover": lambda: pgettext("script field", "voice-over"),
    "on_screen_text": lambda: pgettext("script field", "on-screen text"),
    "fact references": lambda: pgettext("script field", "fact references"),
}
SCENE_PATTERN = re.compile(r"^scene (\d+) (\w+)$")


@register.filter
def flag_location(location):
    """Turn a stored location such as "scene 2 voiceover" into readable text."""
    match = SCENE_PATTERN.match(location or "")
    if match:
        field = FIELD_LABELS.get(match.group(2))
        return gettext("scene %(number)s, %(field)s") % {
            "number": match.group(1), "field": field() if field else match.group(2)}
    label = FIELD_LABELS.get(location)
    return label() if label else location


@register.filter
def flag_message(flag):
    """The flag's message, built from its code so it follows the user's language."""
    code, text = flag.get("code"), flag.get("text", "")
    if code == "unsupported_number":
        return gettext("The number “%(text)s” is not in your confirmed information.") % {"text": text}
    if code == "unsupported_claim":
        return gettext("“%(text)s” may be a claim that is not in your confirmed information.") % {"text": text}
    return gettext(flag.get("message", ""))
