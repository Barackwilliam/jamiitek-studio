"""Queuing and running video renders in the background worker."""

import logging
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.business_profiles.models import FactKey, ProfileFact
from apps.creative_assets.models import Asset

from .ffmpeg import FFmpegError
from .models import VideoRender
from .render import PROFILES, PlanError, render_video, validate_plan

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=30)
DEFAULT_BRAND_COLOR = "#0b6e4f"


class RenderAlreadyRunning(Exception):
    pass


def build_plan(script, *, images, captions=True, end_card=True):
    """Snapshot the approved script into scenes; images are used in order and repeat."""
    scenes = []
    image_ids = [image.pk for image in images]
    for index, scene in enumerate(script.data.get("scenes", [])):
        scenes.append({
            "duration": max(2, min(15, int(scene.get("duration_seconds") or 5))),
            "on_screen_text": scene.get("on_screen_text", ""),
            "caption": scene.get("voiceover", "") if captions else "",
            "image_id": image_ids[index % len(image_ids)] if image_ids else None,
        })
    return {
        "scenes": scenes,
        "end_card": end_card,
        "end_card_text": script.data.get("call_to_action", "") if end_card else "",
    }


def check_plan(plan, voiceover=None):
    """Validate timing with the same rules the renderer uses. Raises PlanError."""
    scenes = list(plan["scenes"])
    if plan.get("end_card"):
        scenes.append({"duration": 3})
    return validate_plan(scenes, voiceover.duration if voiceover else None)


def request_render(project, **fields):
    if project.videos.filter(status__in=VideoRender.ACTIVE_STATUSES).exists():
        raise RenderAlreadyRunning()
    try:
        with transaction.atomic():
            return VideoRender.objects.create(project=project, **fields)
    except IntegrityError:
        raise RenderAlreadyRunning()


def claim_next_render():
    for pk in VideoRender.objects.filter(status=VideoRender.Status.QUEUED).order_by(
            "created_at", "id").values_list("pk", flat=True)[:5]:
        if VideoRender.objects.filter(pk=pk, status=VideoRender.Status.QUEUED).update(
                status=VideoRender.Status.RUNNING, started_at=timezone.now()):
            return VideoRender.objects.select_related("project", "music", "voiceover").get(pk=pk)
    return None


def fail_stale_renders():
    return VideoRender.objects.filter(
        status=VideoRender.Status.RUNNING, started_at__lt=timezone.now() - STALE_AFTER
    ).update(status=VideoRender.Status.FAILED, error_code="interrupted",
             error_message="Rendering was interrupted. Please try again.", finished_at=timezone.now())


def _read(field):
    with field.open("rb") as handle:
        return handle.read()


def _local_path(field, folder):
    """FFmpeg needs a file path; copy from storage into the render's temp folder."""
    target = Path(tempfile.mkdtemp(prefix="jamii-audio-", dir=folder)) / "track.m4a"
    target.write_bytes(_read(field))
    return target


def run_render(render):
    project = render.project
    workdir = tempfile.mkdtemp(prefix="jamii-job-")

    def progress(text):
        VideoRender.objects.filter(pk=render.pk).update(progress=text[:200])

    try:
        assets = {a.pk: a for a in Asset.objects.filter(project=project)}
        plan = []
        for scene in render.plan.get("scenes", []):
            asset = assets.get(scene.get("image_id"))
            plan.append({**scene, "photo_bytes": _read(asset.file) if asset else None})
        logo = Asset.objects.filter(project=project, kind=Asset.Kind.LOGO, rights_confirmed=True).first()
        brand = ProfileFact.objects.filter(profile__project=project, key=FactKey.BRAND_COLOR,
                                           status=ProfileFact.Status.CONFIRMED).first()
        brand_color = brand.value if brand and len(brand.value) == 7 else DEFAULT_BRAND_COLOR

        music_path = _local_path(render.music.file, workdir) if render.music else None
        voice_path = _local_path(render.voiceover.file, workdir) if render.voiceover else None
        end_card = render.plan.get("end_card")

        data, info = render_video(
            plan, profile=PROFILES[render.quality], aspect=render.aspect, brand_color=brand_color,
            logo_bytes=_read(logo.file) if (logo and end_card) else None,
            end_card_text=render.plan.get("end_card_text", "") if end_card else "",
            music_path=music_path, voice_path=voice_path,
            voice_duration=render.voiceover.duration if render.voiceover else None,
            progress=progress,
        )
        render.file.save("video.mp4", ContentFile(data), save=False)
        render.width, render.height = info["width"], info["height"]
        render.duration, render.size_bytes = info["duration"], len(data)
        render.status = VideoRender.Status.COMPLETED
        render.progress = ""
    except (PlanError, FFmpegError) as exc:
        render.status = VideoRender.Status.FAILED
        render.error_code = "plan" if isinstance(exc, PlanError) else "ffmpeg"
        render.error_message = exc.message[:500]
    except Exception:
        logger.exception("Render %s crashed", render.pk)
        render.status = VideoRender.Status.FAILED
        render.error_code = "internal_error"
        render.error_message = "Something went wrong on our side. Please try again later."
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    render.finished_at = timezone.now()
    render.save()
    return render
