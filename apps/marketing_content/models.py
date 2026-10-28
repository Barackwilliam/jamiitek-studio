from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone


class MarketingBrief(models.Model):
    """What the user wants to create: goal, audience, language, format."""

    class Objective(models.TextChoices):
        AWARENESS = "awareness", _("Make more people know the business")
        PRODUCT = "product", _("Promote a product")
        SERVICE = "service", _("Promote a service")
        LEADS = "leads", _("Get enquiries or bookings")
        SALES = "sales", _("Increase sales")
        EVENT = "event", _("Promote an event")

    class Language(models.TextChoices):
        SWAHILI = "sw", _("Kiswahili")
        ENGLISH = "en", _("English")

    class Tone(models.TextChoices):
        FRIENDLY = "friendly", _("Friendly")
        PROFESSIONAL = "professional", _("Professional")
        ENERGETIC = "energetic", _("Energetic")
        WARM = "warm", _("Warm and personal")
        LUXURY = "luxury", _("Premium")

    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", _("Instagram Reels")
        TIKTOK = "tiktok", _("TikTok")
        FACEBOOK = "facebook", _("Facebook")
        WHATSAPP = "whatsapp", _("WhatsApp Status")
        YOUTUBE = "youtube", _("YouTube")
        WEBSITE = "website", _("Website")

    DURATION_CHOICES = [(15, _("15 seconds")), (30, _("30 seconds")), (60, _("60 seconds"))]

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="briefs")
    objective = models.CharField(max_length=20, choices=Objective.choices)
    audience = models.CharField(max_length=300)
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.SWAHILI)
    tone = models.CharField(max_length=20, choices=Tone.choices, default=Tone.FRIENDLY)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    duration_seconds = models.PositiveSmallIntegerField(choices=DURATION_CHOICES, default=30)
    # The user's wishes for this content. Instructions, never business facts.
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.get_objective_display()} · {self.get_platform_display()}"

    def get_absolute_url(self):
        return reverse("marketing_content:brief", args=[self.project_id, self.pk])


class GenerationJob(models.Model):
    """A queued request to the AI provider, processed by the worker."""

    class Kind(models.TextChoices):
        CONCEPTS = "concepts", _("Concepts")
        SCRIPT = "script", _("Script")

    class Status(models.TextChoices):
        QUEUED = "queued", _("Waiting to start")
        RUNNING = "running", _("Writing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    ACTIVE_STATUSES = (Status.QUEUED, Status.RUNNING)

    brief = models.ForeignKey(MarketingBrief, on_delete=models.CASCADE, related_name="jobs")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    concept = models.ForeignKey(
        "ContentDraft", on_delete=models.CASCADE, null=True, blank=True, related_name="script_jobs"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    error_code = models.CharField(max_length=40, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    provider = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=200, blank=True)
    usage = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            # One job at a time per brief: repeated clicks cannot spend the
            # free AI quota twice.
            models.UniqueConstraint(
                fields=["brief"],
                condition=models.Q(status__in=["queued", "running"]),
                name="one_active_generation_per_brief",
            )
        ]

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def waiting_too_long(self):
        return (
            self.status == self.Status.QUEUED
            and (timezone.now() - self.created_at).total_seconds() > 30
        )


class ContentDraft(models.Model):
    """An AI-written concept or script, which the user can edit and approve.

    `facts` is a snapshot of the confirmed facts given to the AI, keyed by
    reference ("F1", "F2", ...), so references stay meaningful even if the
    profile changes later. `flags` lists possible claims that are not
    supported by those facts.
    """

    class Kind(models.TextChoices):
        CONCEPT = "concept", _("Concept")
        SCRIPT = "script", _("Script")

    class Status(models.TextChoices):
        GENERATED = "generated", _("AI draft")
        EDITED = "edited", _("Edited by you")
        APPROVED = "approved", _("Approved")

    brief = models.ForeignKey(MarketingBrief, on_delete=models.CASCADE, related_name="drafts")
    job = models.ForeignKey(GenerationJob, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name="drafts")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    concept = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="scripts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.GENERATED)
    data = models.JSONField(default=dict)
    facts = models.JSONField(default=list)
    flags = models.JSONField(default=list, blank=True)
    provider = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=200, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return self.title

    @property
    def title(self):
        return self.data.get("title") or self.get_kind_display()

    def get_absolute_url(self):
        return reverse("marketing_content:script", args=[self.brief.project_id, self.pk])

    def fact_lookup(self):
        return {fact["ref"]: fact for fact in self.facts}


class DraftRevision(models.Model):
    """An earlier version of a draft, saved before each edit or restore."""

    MAX_PER_DRAFT = 20

    draft = models.ForeignKey(ContentDraft, on_delete=models.CASCADE, related_name="revisions")
    data = models.JSONField()
    status = models.CharField(max_length=20, choices=ContentDraft.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    @classmethod
    def save_from(cls, draft):
        """Store the draft's current content, keeping only the newest revisions."""
        cls.objects.create(draft=draft, data=draft.data, status=draft.status)
        old = cls.objects.filter(draft=draft).order_by("-created_at", "-id")[cls.MAX_PER_DRAFT:]
        cls.objects.filter(pk__in=[r.pk for r in old]).delete()
