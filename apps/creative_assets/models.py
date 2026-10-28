import hashlib
import uuid

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


def random_path(instance, filename, folder):
    # Random names: user-supplied file names are never used for storage.
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"projects/{instance.project_id}/{folder}/{uuid.uuid4().hex}.{extension}"


def asset_upload_to(instance, filename):
    return random_path(instance, filename, "assets")


def thumbnail_upload_to(instance, filename):
    return random_path(instance, filename, "thumbnails")


def poster_upload_to(instance, filename):
    return random_path(instance, filename, "posters")


class Asset(models.Model):
    """An image the project may use, with where it came from and the user's rights confirmation."""

    class Kind(models.TextChoices):
        IMAGE = "image", _("Photo or image")
        LOGO = "logo", _("Logo")

    class Origin(models.TextChoices):
        UPLOAD = "upload", _("Uploaded by you")
        WEBSITE = "website", _("From your website")

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="assets")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.IMAGE)
    origin = models.CharField(max_length=20, choices=Origin.choices)
    file = models.FileField(upload_to=asset_upload_to, max_length=300)
    thumbnail = models.FileField(upload_to=thumbnail_upload_to, max_length=300)
    original_name = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(max_length=2048, blank=True)
    alt_text = models.CharField(max_length=300, blank=True)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    # The user confirmed they own the image or have permission to use it.
    rights_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "sha256"], name="unique_asset_content_per_project")
        ]

    def __str__(self):
        return self.original_name or self.source_url or f"Asset {self.pk}"

    def file_url(self):
        return reverse("creative_assets:asset_file", args=[self.project_id, self.pk, "full"])

    def thumbnail_url(self):
        return reverse("creative_assets:asset_file", args=[self.project_id, self.pk, "thumb"])

    @classmethod
    def create_from_processed(cls, *, project, processed, origin, **fields):
        asset = cls(
            project=project, origin=origin, width=processed.width, height=processed.height,
            size_bytes=len(processed.content),
            sha256=hashlib.sha256(processed.content).hexdigest(), **fields,
        )
        name = f"image.{processed.extension}"
        asset.file.save(name, ContentFile(processed.content), save=False)
        asset.thumbnail.save(name, ContentFile(processed.thumbnail), save=False)
        asset.save()
        return asset

    def delete_files(self):
        for field in (self.file, self.thumbnail):
            if field:
                field.delete(save=False)


class ImageImportJob(models.Model):
    """Images from the analyzed website that the user chose to import."""

    class Status(models.TextChoices):
        QUEUED = "queued", _("Waiting to start")
        RUNNING = "running", _("Importing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    ACTIVE_STATUSES = (Status.QUEUED, Status.RUNNING)

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="image_imports")
    urls = models.JSONField(default=list)
    # [{"url": ..., "status": "imported"|"failed"|"duplicate", "message": ...}]
    results = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project"], condition=models.Q(status__in=["queued", "running"]),
                name="one_active_image_import_per_project",
            )
        ]

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES


class Poster(models.Model):
    class Format(models.TextChoices):
        SQUARE = "square", _("Square 1:1 (1080 × 1080)")
        PORTRAIT = "portrait", _("Vertical 9:16 (1080 × 1920)")
        LANDSCAPE = "landscape", _("Horizontal 16:9 (1920 × 1080)")

    SIZES = {"square": (1080, 1080), "portrait": (1080, 1920), "landscape": (1920, 1080)}

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="posters")
    script = models.ForeignKey("marketing_content.ContentDraft", on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="posters")
    background = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    logo = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    format = models.CharField(max_length=20, choices=Format.choices, default=Format.SQUARE)
    headline = models.CharField(max_length=120)
    subtext = models.CharField(max_length=200, blank=True)
    call_to_action = models.CharField(max_length=80, blank=True)
    brand_color = models.CharField(max_length=7, default="#0b6e4f")
    file = models.FileField(upload_to=poster_upload_to, max_length=300)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    # Possible unsupported claims in the poster text (see marketing_content.validation).
    flags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.headline

    def get_absolute_url(self):
        return reverse("creative_assets:poster", args=[self.project_id, self.pk])

    def file_url(self):
        return reverse("creative_assets:poster_file", args=[self.project_id, self.pk])
