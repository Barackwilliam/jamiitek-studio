from django.contrib import admin

from .models import WorkerHeartbeat


@admin.register(WorkerHeartbeat)
class WorkerHeartbeatAdmin(admin.ModelAdmin):
    list_display = ["name", "last_seen", "jobs_processed", "last_error_at"]
    readonly_fields = ["name", "last_seen", "jobs_processed", "last_error_at"]
