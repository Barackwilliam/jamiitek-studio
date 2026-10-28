from django.db import models
from django.urls import reverse


class FactKey(models.TextChoices):
    """The kinds of business information the profile can hold."""

    BUSINESS_NAME = "business_name", "Business name"
    DESCRIPTION = "description", "Description"
    OFFERING = "offering", "Product or service"
    PRICE = "price", "Price"
    PHONE = "phone", "Phone number"
    EMAIL = "email", "Email address"
    ADDRESS = "address", "Address"
    OPENING_HOURS = "opening_hours", "Opening hours"
    SOCIAL = "social", "Social media"
    LOGO = "logo", "Logo"
    BRAND_COLOR = "brand_color", "Brand colour"
    OTHER = "other", "Other information"


# Keys where a business normally has a single value; differing suggestions
# for these are shown as a conflict the user should resolve.
SINGLE_VALUE_KEYS = {FactKey.BUSINESS_NAME, FactKey.DESCRIPTION, FactKey.ADDRESS, FactKey.LOGO}

# Information content creation will need; missing items are pointed out.
ESSENTIAL_KEYS = [
    FactKey.BUSINESS_NAME,
    FactKey.DESCRIPTION,
    FactKey.OFFERING,
    FactKey.PHONE,
    FactKey.ADDRESS,
]

MAX_VALUE_LENGTH = {FactKey.DESCRIPTION: 1000, FactKey.OTHER: 1000}
DEFAULT_MAX_VALUE_LENGTH = 300


class BusinessProfile(models.Model):
    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="business_profile"
    )
    # The analysis the current website suggestions came from.
    source_analysis = models.ForeignKey(
        "website_analyzer.WebsiteAnalysis", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.project}"

    def get_absolute_url(self):
        return reverse("business_profiles:detail", args=[self.project_id])


class ProfileFact(models.Model):
    """One piece of business information and where it came from.

    Website facts start as suggestions; only facts the user confirmed or
    entered are treated as approved for content creation.
    """

    class Source(models.TextChoices):
        WEBSITE = "website", "Found on the website"
        USER = "user", "Entered by you"

    class Status(models.TextChoices):
        SUGGESTED = "suggested", "Needs your review"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"

    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="facts")
    key = models.CharField(max_length=30, choices=FactKey.choices)
    value = models.TextField()
    # Lower-cased, whitespace-collapsed value used to detect duplicates.
    normalized_value = models.TextField(editable=False)
    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUGGESTED)
    # [{"url": ..., "detail": ...}] for website facts.
    evidence = models.JSONField(default=list, blank=True)
    edited_by_user = models.BooleanField(default=False)
    # The website's wording before the user edited it, so the original is
    # not suggested again after an edit.
    original_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "key", "normalized_value"], name="unique_fact_value_per_key"
            )
        ]

    def __str__(self):
        return f"{self.get_key_display()}: {self.value}"

    def save(self, *args, **kwargs):
        self.normalized_value = normalize_value(self.value)
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == self.Status.CONFIRMED


def normalize_value(value):
    return " ".join((value or "").split()).casefold()


def max_length_for(key):
    return MAX_VALUE_LENGTH.get(key, DEFAULT_MAX_VALUE_LENGTH)
