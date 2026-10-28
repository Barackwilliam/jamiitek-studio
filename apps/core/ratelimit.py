"""Simple database-backed rate limiting for sensitive actions.

Used for log-in and sign-up so passwords cannot be guessed quickly. Only
hashes of usernames and IP addresses are stored, never the values
themselves. The database is used rather than a cache so limits hold across
several server processes without extra infrastructure (DEC-016).
"""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import RateLimitEvent


def _digest(action, key):
    secret = settings.SECRET_KEY.encode()
    return hashlib.sha256(secret + b"|" + action.encode() + b"|" + key.casefold().encode()).hexdigest()


def client_ip(request):
    # Behind a reverse proxy, REMOTE_ADDR is the proxy; configure the proxy
    # to pass the client address before relying on per-IP limits there.
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def is_limited(action, key, limit, window):
    since = timezone.now() - window
    return RateLimitEvent.objects.filter(
        action=action, key_hash=_digest(action, key), created_at__gte=since
    ).count() >= limit


def record(action, key):
    RateLimitEvent.objects.create(action=action, key_hash=_digest(action, key))


def clear(action, key):
    RateLimitEvent.objects.filter(action=action, key_hash=_digest(action, key)).delete()


def delete_old_events(older_than=timedelta(days=1)):
    return RateLimitEvent.objects.filter(created_at__lt=timezone.now() - older_than).delete()[0]
