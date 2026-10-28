from django.conf import settings
from django.db import models
from django.urls import reverse


class Project(models.Model):
    """A marketing workspace for one business, owned by one user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=120)
    business_name = models.CharField(max_length=200, blank=True)
    # Stored only after passing url_safety.validate_public_url.
    website_url = models.URLField(max_length=2048, blank=True)
    # Information typed by the user (FR-02A); always treated as user-provided.
    business_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.pk])
