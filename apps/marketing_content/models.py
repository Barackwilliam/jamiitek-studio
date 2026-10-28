from django.db import models
from django.urls import reverse
from django.utils import timezone


class MarketingBrief(models.Model):
    """What the user wants to create: goal, audience, language, format."""

    class Objective(models.TextChoices):
        AWARENESS = "awareness", "Make more people know the business"
        PRODUCT = "product", "Promote a product"
        SERVICE = "service", "Promote a service"
        LEADS = "leads", "Get enquiries or bookings"
        SALES = "sales", "Increase sales"
        EVENT = "event", "Promote an event"

    class Language(models.TextChoices):
        SWAHILI = "sw", "Kiswahili"
        ENGLISH = "en", "English"

    class Tone(models.TextChoices):
        FRIENDLY = "friendly", "Friendly"
        PROFESSIONAL = "professional", "Professional"
        ENERGETIC = "energetic", "Energetic"
        WARM = "warm", "Warm and personal"
        LUXURY = "luxury", "Premium"

    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram Reels"
        TIKTOK = "tiktok", "TikTok"
        FACEBOOK = "facebook", "Facebook"
        WHATSAPP = "whatsapp", "WhatsApp Status"
        YOUTUBE = "youtube", "YouTube"
        WEBSITE = "website", "Website"

    DURATION_CHOICES = [(15, "15 seconds"), (30, "30 seconds"), (60, "60 seconds")]

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
        CONCEPTS = "concepts", "Concepts"
        SCRIPT = "script", "Script"

    class Status(models.TextChoices):
        QUEUED = "queued", "Waiting to start"
        RUNNING = "running", "Writing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

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
        CONCEPT = "concept", "Concept"
        SCRIPT = "script", "Script"

    class Status(models.TextChoices):
        GENERATED = "generated", "AI draft"
        EDITED = "edited", "Edited by you"
        APPROVED = "approved", "Approved"

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
