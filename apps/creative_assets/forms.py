from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .images import InvalidImage, process_image
from .models import Asset, Poster
from .posters import HEX_COLOR

RIGHTS_LABEL = _("I own these images or have permission to use them in advertising.")


class UploadForm(forms.Form):
    image = forms.FileField(label=_("Image file"), help_text=_("JPEG, PNG, WebP or GIF, up to 8 MB."))
    kind = forms.ChoiceField(label=_("Type"), choices=Asset.Kind.choices, initial=Asset.Kind.IMAGE)
    alt_text = forms.CharField(label=_("Short description"), max_length=300, required=False,
                               help_text=_("What the image shows, for example: Pilau served at a wedding."))
    rights_confirmed = forms.BooleanField(label=RIGHTS_LABEL)

    def clean_image(self):
        upload = self.cleaned_data["image"]
        # Check the size before reading the file into memory.
        if upload.size > settings.MAX_IMAGE_BYTES:
            raise forms.ValidationError(
                _("The image is larger than %(mb)d MB."), params={"mb": settings.MAX_IMAGE_BYTES // (1024 * 1024)})
        try:
            self.processed = process_image(upload.read(), settings.MAX_IMAGE_BYTES)
        except InvalidImage as exc:
            raise forms.ValidationError(exc.message) from exc
        return upload


class ImportForm(forms.Form):
    rights_confirmed = forms.BooleanField(label=RIGHTS_LABEL)


class PosterForm(forms.ModelForm):
    class Meta:
        model = Poster
        fields = ["format", "background", "logo", "headline", "subtext", "call_to_action", "brand_color"]
        labels = {
            "background": _("Photo"), "logo": _("Logo"), "headline": _("Headline"),
            "subtext": _("Supporting text"), "call_to_action": _("Button text"),
            "brand_color": _("Brand colour"),
        }
        widgets = {"brand_color": forms.TextInput(attrs={"type": "color"})}

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        usable = project.assets.filter(rights_confirmed=True)
        self.fields["background"].queryset = usable.filter(kind=Asset.Kind.IMAGE)
        self.fields["background"].required = False
        self.fields["background"].empty_label = _("No photo (brand colour background)")
        self.fields["logo"].queryset = usable.filter(kind=Asset.Kind.LOGO)
        self.fields["logo"].required = False
        self.fields["logo"].empty_label = _("No logo")
        for name in ("background", "logo"):
            self.fields[name].label_from_instance = lambda asset: asset.alt_text or str(asset)

    def clean_brand_color(self):
        value = self.cleaned_data["brand_color"].lower()
        if not HEX_COLOR.match(value):
            raise forms.ValidationError(_("Choose a colour such as #0b6e4f."))
        return value
