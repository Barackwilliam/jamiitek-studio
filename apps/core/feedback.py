"""Showing form errors as messages after a redirect."""

from django.contrib import messages
from django.forms.forms import NON_FIELD_ERRORS
from django.utils.translation import gettext as _


def form_errors_as_messages(request, form):
    """Add each form error as a message, naming the field it belongs to.

    Used where a small form posts from a larger page and redirects back, so
    the error cannot be shown next to the field itself.
    """
    for name, errors in form.errors.items():
        label = form.fields[name].label if name != NON_FIELD_ERRORS and name in form.fields else None
        for error in errors:
            if label:
                messages.error(request, _("%(field)s: %(error)s") % {"field": label, "error": error})
            else:
                messages.error(request, error)
