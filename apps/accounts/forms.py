from datetime import timedelta

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from apps.core import ratelimit

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_LIMIT_PER_USERNAME = 5
LOGIN_LIMIT_PER_IP = 20

LOCKED_MESSAGE = _("Too many failed attempts. Please wait 15 minutes and try again.")


class RateLimitedAuthenticationForm(AuthenticationForm):
    """Blocks password guessing per username and per IP address.

    The message is the same whether or not the username exists, so it
    does not reveal which accounts exist.
    """

    def clean(self):
        username = (self.data.get("username") or "").strip()
        ip = ratelimit.client_ip(self.request) if self.request else "unknown"
        if (ratelimit.is_limited("login-user", username, LOGIN_LIMIT_PER_USERNAME, LOGIN_WINDOW)
                or ratelimit.is_limited("login-ip", ip, LOGIN_LIMIT_PER_IP, LOGIN_WINDOW)):
            raise forms.ValidationError(LOCKED_MESSAGE, code="rate_limited")
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            ratelimit.record("login-user", username)
            ratelimit.record("login-ip", ip)
            raise
        ratelimit.clear("login-user", username)
        return cleaned
