from django import forms
from django.utils.translation import gettext_lazy as _

from .models import FactKey, ProfileFact, max_length_for, normalize_value


class FactValueForm(forms.Form):
    value = forms.CharField(label=_("Value"), widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, profile=None, key=None, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.key = key
        self.instance = instance

    def clean_value(self):
        # In AddFactForm the key field is cleaned first and takes precedence.
        key = self.cleaned_data.get("key", self.key)
        value = " ".join(self.cleaned_data["value"].split())
        if not value:
            raise forms.ValidationError(_("Enter a value."))
        limit = max_length_for(key)
        if len(value) > limit:
            raise forms.ValidationError(
                _("Keep this under %(limit)d characters."), params={"limit": limit}
            )
        if self.profile is not None:
            duplicates = ProfileFact.objects.filter(
                profile=self.profile, key=key, normalized_value=normalize_value(value)
            )
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(_("This value is already in the profile."))
        return value


class AddFactForm(FactValueForm):
    key = forms.ChoiceField(label=_("Type of information"), choices=FactKey.choices)

    field_order = ["key", "value"]
