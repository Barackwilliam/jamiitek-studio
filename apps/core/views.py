import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


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


@require_safe
@never_cache
def health(request):
    """Report whether the application and its database can serve requests.

    The response deliberately contains no error details, versions, or
    configuration, because this endpoint is public.
    """
    database_ok = _database_is_available()
    return JsonResponse(
        {
            "status": "ok" if database_ok else "error",
            "checks": {"database": "ok" if database_ok else "error"},
        },
        status=200 if database_ok else 503,
    )
