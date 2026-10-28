import hashlib

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone

from apps.creative_assets.models import random_path


def audio_upload_to(instance, filename):
    return random_path(instance, filename, "audio")


def video_upload_to(instance, filename):
    return random_path(instance, filename, "videos")


class AudioTrack(models.Model):
    class Kind(models.TextChoices):
        MUSIC = "music", _("Background music")
        VOICEOVER = "voiceover", _("Voice-over recording")

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="audio_tracks")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    file = models.FileField(upload_to=audio_upload_to, max_length=300)
    original_name = models.CharField(max_length=200, blank=True)
    duration = models.FloatField()
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    rights_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "sha256"], name="unique_audio_content_per_project")
        ]

    def __str__(self):
        return f"{self.original_name or self.get_kind_display()} ({self.duration:.0f} s)"

    @classmethod
    def create_from_processed(cls, *, project, processed, **fields):
        track = cls(project=project, duration=processed.duration, size_bytes=len(processed.content),
                    sha256=hashlib.sha256(processed.content).hexdigest(), **fields)
        track.file.save("audio.m4a", ContentFile(processed.content), save=False)
        track.save()
        return track

    def file_url(self):
        return reverse("media_production:audio_file", args=[self.project_id, self.pk])


class VideoRender(models.Model):
    class Aspect(models.TextChoices):
        PORTRAIT = "portrait", _("Vertical 9:16 (Reels, TikTok, Status)")
        SQUARE = "square", _("Square 1:1")
        LANDSCAPE = "landscape", _("Horizontal 16:9 (YouTube, website)")

    class Quality(models.TextChoices):
        PREVIEW = "preview", _("Preview (fast, 540p)")
        FINAL = "final", _("Final (1080p, slower)")

    class Status(models.TextChoices):
        QUEUED = "queued", _("Waiting to start")
        RUNNING = "running", _("Rendering")
        COMPLETED = "completed", _("Ready")
        FAILED = "failed", _("Failed")

    ACTIVE_STATUSES = (Status.QUEUED, Status.RUNNING)

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="videos")
    script = models.ForeignKey("marketing_content.ContentDraft", on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="videos")
    aspect = models.CharField(max_length=20, choices=Aspect.choices, default=Aspect.PORTRAIT)
    quality = models.CharField(max_length=20, choices=Quality.choices, default=Quality.PREVIEW)
    music = models.ForeignKey(AudioTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    voiceover = models.ForeignKey(AudioTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    # Snapshot of what to render: scenes with texts, durations and image ids,
    # plus the end card, so later edits to the script do not change this video.
    plan = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress = models.CharField(max_length=200, blank=True)
    error_code = models.CharField(max_length=40, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    file = models.FileField(upload_to=video_upload_to, max_length=300, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    size_bytes = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # One render at a time per project; rendering is heavy on a small computer.
            models.UniqueConstraint(fields=["project"], condition=models.Q(status__in=["queued", "running"]),
                                    name="one_active_render_per_project")
        ]

    def __str__(self):
        return f"{self.get_aspect_display()} · {self.get_quality_display()}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def waiting_too_long(self):
        return self.status == self.Status.QUEUED and (timezone.now() - self.created_at).total_seconds() > 30

    def get_absolute_url(self):
        return reverse("media_production:video", args=[self.project_id, self.pk])

    def file_url(self):
        return reverse("media_production:video_file", args=[self.project_id, self.pk])
