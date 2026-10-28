from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.creative_assets.models import Asset
from apps.marketing_content.models import ContentDraft

from .audio import InvalidAudio, process_audio
from .models import AudioTrack, VideoRender

RIGHTS_LABEL = _("I own this recording or have a licence to use it in advertising.")


class AudioUploadForm(forms.Form):
    audio = forms.FileField(label=_("Audio file"), help_text=_("MP3, M4A, WAV or OGG, up to 15 MB and 10 minutes."))
    kind = forms.ChoiceField(label=_("Type"), choices=AudioTrack.Kind.choices)
    rights_confirmed = forms.BooleanField(label=RIGHTS_LABEL)

    def clean_audio(self):
        upload = self.cleaned_data["audio"]
        if upload.size > settings.MAX_AUDIO_BYTES:
            raise forms.ValidationError(
                _("The file is larger than %(mb)d MB."), params={"mb": settings.MAX_AUDIO_BYTES // (1024 * 1024)})
        try:
            self.processed = process_audio(upload.read())
        except InvalidAudio as exc:
            raise forms.ValidationError(exc.message) from exc
        return upload


class RenderForm(forms.Form):
    script = forms.ModelChoiceField(label=_("Approved script"), queryset=ContentDraft.objects.none())
    aspect = forms.ChoiceField(label=_("Format"), choices=VideoRender.Aspect.choices)
    quality = forms.ChoiceField(label=_("Quality"), choices=VideoRender.Quality.choices,
                                help_text=_("Make a preview first; final quality takes several times longer."))
    images = forms.ModelMultipleChoiceField(
        label=_("Photos (used in order, one per scene)"), queryset=Asset.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Without photos, scenes use your brand colour."))
    music = forms.ModelChoiceField(label=_("Background music"), queryset=AudioTrack.objects.none(),
                                   required=False, empty_label=_("No music"))
    voiceover = forms.ModelChoiceField(label=_("Voice-over"), queryset=AudioTrack.objects.none(),
                                       required=False, empty_label=_("No voice-over"))
    captions = forms.BooleanField(label=_("Show the narration as captions"), required=False, initial=True)
    end_card = forms.BooleanField(label=_("End with logo and call to action"), required=False, initial=True)

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["script"].queryset = ContentDraft.objects.filter(
            brief__project=project, kind=ContentDraft.Kind.SCRIPT, status=ContentDraft.Status.APPROVED)
        self.fields["script"].label_from_instance = lambda draft: draft.title
        self.fields["images"].queryset = project.assets.filter(kind=Asset.Kind.IMAGE, rights_confirmed=True)
        self.fields["images"].label_from_instance = lambda asset: asset.alt_text or str(asset)
        tracks = project.audio_tracks.filter(rights_confirmed=True)
        self.fields["music"].queryset = tracks.filter(kind=AudioTrack.Kind.MUSIC)
        self.fields["voiceover"].queryset = tracks.filter(kind=AudioTrack.Kind.VOICEOVER)
