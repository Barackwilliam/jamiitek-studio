from django.db import models


class RateLimitEvent(models.Model):
    """One counted attempt of a rate-limited action (see ratelimit.py)."""

    action = models.CharField(max_length=40)
    key_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["action", "key_hash", "created_at"])]


class WorkerHeartbeat(models.Model):
    """Updated by `run_worker` on every loop so the health check can tell if it is running."""

    name = models.CharField(max_length=100, unique=True)
    last_seen = models.DateTimeField()
    jobs_processed = models.PositiveIntegerField(default=0)
    last_error_at = models.DateTimeField(null=True, blank=True)
