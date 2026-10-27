from django import forms
from django.utils.translation import gettext_lazy as _

from apps.website_analyzer.url_safety import UnsafeURLError, validate_public_url

from .models import Project

MAX_BUSINESS_DETAILS_LENGTH = 5000


class ProjectForm(forms.ModelForm):
    # A plain CharField so users can type "example.com"; the value is
    # normalized and safety-checked in clean_website_url.
    website_url = forms.CharField(
        label=_("Website address"),
        required=False,
        max_length=2048,
        help_text=_("For example: example.com. Leave empty if you have no website."),
        widget=forms.TextInput(attrs={"inputmode": "url", "autocomplete": "url"}),
    )
    business_details = forms.CharField(
        label=_("Business details"),
        required=False,
        max_length=MAX_BUSINESS_DETAILS_LENGTH,
        help_text=_("What you sell, who your customers are, and anything else we should know."),
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    class Meta:
        model = Project
        fields = ["name", "business_name", "website_url", "business_details"]
        labels = {"name": _("Project name"), "business_name": _("Business name")}

    def clean_website_url(self):
        raw = self.cleaned_data["website_url"].strip()
        if not raw:
            return ""
        try:
            return validate_public_url(raw).url
        except UnsafeURLError as exc:
            raise forms.ValidationError(exc.message, code=exc.code) from exc

    def clean(self):
        cleaned = super().clean()
        if (
            not self.errors
            and not cleaned.get("website_url")
            and not cleaned.get("business_details", "").strip()
        ):
            raise forms.ValidationError(
                _("Enter a website address or describe your business."),
                code="no_source",
            )
        return cleaned
