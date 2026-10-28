from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone


class WebsiteAnalysis(models.Model):
    """One run of website analysis for a project, processed by the worker."""

    class Status(models.TextChoices):
        QUEUED = "queued", _("Waiting to start")
        RUNNING = "running", _("Running")
        COMPLETED = "completed", _("Completed")
        PARTIAL = "partial", _("Completed with some pages failing")
        FAILED = "failed", _("Failed")

    ACTIVE_STATUSES = (Status.QUEUED, Status.RUNNING)

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="analyses"
    )
    start_url = models.URLField(max_length=2048)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    max_pages = models.PositiveSmallIntegerField(default=8)
    pages_attempted = models.PositiveSmallIntegerField(default=0)
    pages_succeeded = models.PositiveSmallIntegerField(default=0)
    stopped_reason = models.CharField(max_length=40, blank=True)
    error_code = models.CharField(max_length=40, blank=True)
    # Shown to the user; never contains internal details.
    error_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            # At most one queued or running analysis per project, so repeated
            # clicks or two browser tabs cannot start duplicate work.
            models.UniqueConstraint(
                fields=["project"],
                condition=models.Q(status__in=["queued", "running"]),
                name="one_active_analysis_per_project",
            )
        ]

    def __str__(self):
        return f"Analysis of {self.start_url} ({self.status})"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def stopped_message(self):
        return {
            "page_limit": _("Stopped after reaching the limit of pages for one analysis."),
            "time_limit": _("Stopped after reaching the time limit for one analysis."),
        }.get(self.stopped_reason, "")

    @property
    def waiting_too_long(self):
        """True when a queued analysis has not been picked up by a worker."""
        return (
            self.status == self.Status.QUEUED
            and (timezone.now() - self.created_at).total_seconds() > 30
        )

    def get_absolute_url(self):
        return reverse("website_analyzer:detail", args=[self.project_id, self.pk])


class AnalyzedPage(models.Model):
    """The outcome for one page the analysis attempted or skipped."""

    class Status(models.TextChoices):
        SUCCESS = "success", _("Analyzed")
        FAILED = "failed", _("Failed")
        SKIPPED = "skipped", _("Skipped")

    analysis = models.ForeignKey(WebsiteAnalysis, on_delete=models.CASCADE, related_name="pages")
    position = models.PositiveSmallIntegerField()
    url = models.URLField(max_length=2048)
    status = models.CharField(max_length=20, choices=Status.choices)
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    depth = models.PositiveSmallIntegerField(default=0)
    error_code = models.CharField(max_length=40, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    # Observed page content (never inferred). Website text is untrusted data.
    title = models.CharField(max_length=300, blank=True)
    meta_description = models.TextField(blank=True)
    canonical_url = models.URLField(max_length=2048, blank=True)
    language = models.CharField(max_length=20, blank=True)
    theme_color = models.CharField(max_length=30, blank=True)
    open_graph = models.JSONField(default=dict, blank=True)
    headings = models.JSONField(default=list, blank=True)
    text = models.TextField(blank=True)
    text_truncated = models.BooleanField(default=False)
    images = models.JSONField(default=list, blank=True)
    structured_data = models.JSONField(default=list, blank=True)
    links = models.JSONField(default=list, blank=True)
    links_found = models.PositiveIntegerField(default=0)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["analysis", "position"], name="unique_page_position")
        ]

    def __str__(self):
        return self.url

    @property
    def structured_types(self):
        types = []
        for item in self.structured_data:
            value = item.get("@type")
            for name in value if isinstance(value, list) else [value]:
                if isinstance(name, str) and name not in types:
                    types.append(name)
        return types
