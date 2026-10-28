import re

from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _

from .models import MarketingBrief
from .validation import TEXT_LIMITS


class BriefForm(forms.ModelForm):
    notes = forms.CharField(
        label=_("Anything else? (optional)"),
        required=False,
        max_length=1000,
        help_text=_("Your wishes for this content, for example a season or an occasion. "
                    "Write business facts in the business profile instead."),
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = MarketingBrief
        fields = ["objective", "audience", "platform", "duration_seconds", "language", "tone", "notes"]
        labels = {
            "objective": _("Goal"),
            "audience": _("Who is it for?"),
            "platform": _("Where will it be shown?"),
            "duration_seconds": _("Video length"),
            "language": _("Language"),
            "tone": _("Style"),
        }
        help_texts = {"audience": _("For example: families in Dar es Salaam planning a wedding.")}


class ScriptForm(forms.Form):
    title = forms.CharField(label=_("Title"), max_length=TEXT_LIMITS["title"])
    headline = forms.CharField(label=_("Headline"), max_length=TEXT_LIMITS["headline"], required=False)
    caption = forms.CharField(label=_("Caption"), max_length=TEXT_LIMITS["caption"], required=False,
                              widget=forms.Textarea(attrs={"rows": 4}))
    call_to_action = forms.CharField(label=_("Call to action"), max_length=TEXT_LIMITS["call_to_action"],
                                     required=False)
    hashtags = forms.CharField(label=_("Hashtags"), required=False, max_length=400,
                               help_text=_("Separate with spaces or commas."))

    def clean_hashtags(self):
        tags = []
        for tag in re.split(r"[\s,]+", self.cleaned_data["hashtags"]):
            tag = re.sub(r"[^\w]", "", tag.lstrip("#"))[: TEXT_LIMITS["hashtag"]]
            if tag and tag not in tags:
                tags.append(tag)
        return tags[:10]


class SceneForm(forms.Form):
    voiceover = forms.CharField(label=_("Narration"), max_length=TEXT_LIMITS["voiceover"], required=False,
                                widget=forms.Textarea(attrs={"rows": 2}))
    on_screen_text = forms.CharField(label=_("On-screen text"), max_length=TEXT_LIMITS["on_screen_text"],
                                     required=False)
    visual = forms.CharField(label=_("What to show"), max_length=TEXT_LIMITS["visual"], required=False)
    duration_seconds = forms.IntegerField(label=_("Seconds"), min_value=1, max_value=30, initial=5)


SceneFormSet = formset_factory(SceneForm, extra=0, can_delete=True, min_num=1, validate_min=True,
                               max_num=10, validate_max=True)


class ApproveForm(forms.Form):
    checked_claims = forms.BooleanField(
        label=_("I have checked the highlighted claims and they are true for my business."),
        required=False,
    )

    def __init__(self, *args, needs_check=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.needs_check = needs_check

    def clean(self):
        cleaned = super().clean()
        if self.needs_check and not cleaned.get("checked_claims"):
            raise forms.ValidationError(_("Please check the highlighted claims and tick the box."))
        return cleaned
