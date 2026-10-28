import logging
from datetime import timedelta

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import WorkerHeartbeat

logger = logging.getLogger(__name__)

WORKER_STALE_AFTER = timedelta(minutes=2)


@require_safe
def home(request):
    return render(request, "core/home.html")


def _database_is_available():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("Health check: database unavailable")
        return False
    return True


def _worker_status():
    """"ok", "stale" (not seen recently) or "not_seen" (never started)."""
    heartbeat = WorkerHeartbeat.objects.filter(name="default").first()
    if heartbeat is None:
        return "not_seen"
    return "ok" if timezone.now() - heartbeat.last_seen <= WORKER_STALE_AFTER else "stale"


@require_safe
@never_cache
def health(request):
    """Report whether the application and its database can serve requests.

    The web application is healthy when the database works; the worker's
    state is reported separately so a stopped worker is visible without
    marking the website itself as down. No error details, versions or
    configuration are included, because this endpoint is public.
    """
    database_ok = _database_is_available()
    checks = {"database": "ok" if database_ok else "error"}
    if database_ok:
        try:
            checks["worker"] = _worker_status()
        except DatabaseError:
            checks["worker"] = "unknown"
    return JsonResponse(
        {"status": "ok" if database_ok else "error", "checks": checks},
        status=200 if database_ok else 503,
    )
