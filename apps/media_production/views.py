import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from apps.marketing_content.models import ContentDraft
from apps.projects.models import Project

from .ffmpeg import tools_available
from .forms import AudioUploadForm, RenderForm
from .jobs import RenderAlreadyRunning, build_plan, check_plan, request_render
from .models import AudioTrack, VideoRender
from .render import PlanError


def _owned_project(request, project_pk):
    return get_object_or_404(Project, pk=project_pk, owner=request.user)


def _stream(field, filename, download=False):
    try:
        handle = field.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("File missing")
    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type, as_attachment=download, filename=filename)
    response["Cache-Control"] = "private, max-age=300"
    return response


@login_required
@require_safe
def videos(request, project_pk):
    project = _owned_project(request, project_pk)
    return render(request, "media_production/videos.html", {
        "project": project,
        "renders": project.videos.all(),
        "tracks": project.audio_tracks.all(),
        "audio_form": AudioUploadForm(),
        "has_approved_script": ContentDraft.objects.filter(
            brief__project=project, kind="script", status="approved").exists(),
        "ffmpeg_ready": tools_available(),
    })


@login_required
@require_POST
def upload_audio(request, project_pk):
    project = _owned_project(request, project_pk)
    form = AudioUploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            with transaction.atomic():
                AudioTrack.create_from_processed(
                    project=project, processed=form.processed, kind=form.cleaned_data["kind"],
                    original_name=form.cleaned_data["audio"].name[:200], rights_confirmed=True)
            messages.success(request, _("Audio added."))
        except IntegrityError:
            messages.info(request, _("This recording is already in the project."))
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("media_production:videos", project_pk=project.pk)


@login_required
@require_http_methods(["GET", "POST"])
def create_video(request, project_pk):
    project = _owned_project(request, project_pk)
    initial = {}
    if request.GET.get("script", "").isdigit():
        initial["script"] = request.GET["script"]
    form = RenderForm(request.POST or None, initial=initial, project=project)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        plan = build_plan(data["script"], images=list(data["images"]),
                          captions=data["captions"], end_card=data["end_card"])
        try:
            check_plan(plan, data["voiceover"])
            video = request_render(project, script=data["script"], aspect=data["aspect"],
                                   quality=data["quality"], music=data["music"],
                                   voiceover=data["voiceover"], plan=plan)
        except PlanError as exc:
            form.add_error(None, exc.message)
        except RenderAlreadyRunning:
            form.add_error(None, _("A video for this project is already being made. Please wait for it to finish."))
        else:
            messages.success(request, _("Your video is being made."))
            return redirect(video)
    return render(request, "media_production/video_form.html", {
        "project": project, "form": form, "ffmpeg_ready": tools_available(),
    })


@login_required
@require_safe
def video_detail(request, project_pk, pk):
    video = get_object_or_404(VideoRender, pk=pk, project_id=project_pk, project__owner=request.user)
    return render(request, "media_production/video_detail.html", {"project": video.project, "video": video})


@login_required
@require_safe
def video_file(request, project_pk, pk):
    video = get_object_or_404(VideoRender, pk=pk, project_id=project_pk, project__owner=request.user,
                              status=VideoRender.Status.COMPLETED)
    return _stream(video.file, f"video-{video.pk}-{video.aspect}-{video.quality}.mp4",
                   download=request.GET.get("download") == "1")


@login_required
@require_POST
def video_delete(request, project_pk, pk):
    video = get_object_or_404(VideoRender, pk=pk, project_id=project_pk, project__owner=request.user)
    if video.is_active:
        messages.error(request, _("Wait until the video is finished before deleting it."))
        return redirect(video)
    video.delete()
    messages.success(request, _("Video deleted."))
    return redirect("media_production:videos", project_pk=project_pk)


@login_required
@require_safe
def audio_file(request, project_pk, pk):
    track = get_object_or_404(AudioTrack, pk=pk, project_id=project_pk, project__owner=request.user)
    return _stream(track.file, f"audio-{track.pk}.m4a")


@login_required
@require_POST
def audio_delete(request, project_pk, pk):
    track = get_object_or_404(AudioTrack, pk=pk, project_id=project_pk, project__owner=request.user)
    track.delete()
    messages.success(request, _("Audio removed. Videos already made are kept."))
    return redirect("media_production:videos", project_pk=project_pk)
