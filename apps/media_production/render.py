"""Turning a scene plan into a validated MP4.

Steps, all inside a temporary folder that is always removed:
1. For each scene, draw the background and the text layer with Pillow.
2. Render each scene to a short clip: the background zooms slowly while
   the text layer stays still (one FFmpeg run per scene keeps memory low).
3. Join the clips with short cross-fades and add music and/or voice-over.
4. Check the result with FFprobe and a full decode before accepting it.
"""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .ffmpeg import FFmpegError, check_video, ffmpeg
from .frames import background_layer, end_card, text_layer

FADE_SECONDS = 0.5
MIN_SCENE_SECONDS = 2
MAX_SCENE_SECONDS = 15
MAX_TOTAL_SECONDS = 120
MUSIC_VOLUME_WITH_VOICE = 0.18
MUSIC_VOLUME_ALONE = 0.7


@dataclass(frozen=True)
class Profile:
    name: str
    short_side: int
    fps: int
    crf: int
    preset: str


PROFILES = {
    "preview": Profile("preview", 540, 25, 27, "veryfast"),
    "final": Profile("final", 1080, 30, 21, "medium"),
}

ASPECTS = {"portrait": (9, 16), "square": (1, 1), "landscape": (16, 9)}


def frame_size(aspect, profile):
    w, h = ASPECTS[aspect]
    unit = profile.short_side / min(w, h)
    # H.264 with yuv420p needs even dimensions.
    return int(round(w * unit / 2) * 2), int(round(h * unit / 2) * 2)


def total_duration(scenes):
    return sum(s["duration"] for s in scenes) - FADE_SECONDS * max(0, len(scenes) - 1)


class PlanError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def validate_plan(scenes, voice_duration=None):
    """Check timing before spending time on rendering."""
    if not scenes:
        raise PlanError("The script has no scenes.")
    for number, scene in enumerate(scenes, start=1):
        if not MIN_SCENE_SECONDS <= scene["duration"] <= MAX_SCENE_SECONDS:
            raise PlanError(f"Scene {number} must last between {MIN_SCENE_SECONDS} and "
                            f"{MAX_SCENE_SECONDS} seconds.")
    total = total_duration(scenes)
    if total > MAX_TOTAL_SECONDS:
        raise PlanError(f"The video would last {total:.0f} seconds; the limit is {MAX_TOTAL_SECONDS}.")
    if voice_duration and voice_duration > total + 0.5:
        raise PlanError(f"The voice-over lasts {voice_duration:.0f} seconds but the video only "
                        f"{total:.0f}. Lengthen the scenes or shorten the recording.")
    return total


def _render_scene(index, scene, size, profile, workdir):
    width, height = size
    background = workdir / f"bg{index}.jpg"
    overlay = workdir / f"text{index}.png"
    clip = workdir / f"scene{index}.mp4"
    scene["background"].save(background, quality=92)
    scene["text"].save(overlay)
    frames = int(round(scene["duration"] * profile.fps))
    zoom = "min(zoom+0.0007,1.10)" if scene.get("motion", True) else "1"
    ffmpeg([
        "-loop", "1", "-framerate", str(profile.fps), "-i", str(background),
        "-loop", "1", "-framerate", str(profile.fps), "-i", str(overlay),
        "-filter_complex",
        # Upscaling before zoompan avoids visible jitter in the slow zoom.
        f"[0:v]scale={width * 2}:{height * 2},zoompan=z='{zoom}':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={profile.fps}[bg];"
        f"[bg][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", profile.preset, "-crf", str(profile.crf),
        "-threads", str(settings.FFMPEG_THREADS), str(clip),
    ], timeout=300)
    return clip


def _join(clips, scenes, music, voice, output, profile, total):
    inputs = []
    for clip in clips:
        inputs += ["-i", str(clip)]
    filters = []
    last = "0:v"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += scenes[i - 1]["duration"] - FADE_SECONDS
        label = f"x{i}"
        filters.append(f"[{last}][{i}:v]xfade=transition=fade:duration={FADE_SECONDS}:offset={offset:.3f}[{label}]")
        last = label
    filters.append(f"[{last}]format=yuv420p[v]" if len(clips) > 1 else "[0:v]format=yuv420p[v]")

    audio_labels = []
    next_input = len(clips)
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        volume = MUSIC_VOLUME_WITH_VOICE if voice else MUSIC_VOLUME_ALONE
        filters.append(
            f"[{next_input}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={volume},"
            f"afade=t=in:d=1,afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5[music]")
        audio_labels.append("[music]")
        next_input += 1
    if voice:
        inputs += ["-i", str(voice)]
        filters.append(f"[{next_input}:a]apad,atrim=0:{total:.3f},asetpts=PTS-STARTPTS[voice]")
        audio_labels.append("[voice]")
    if len(audio_labels) == 2:
        filters.append("[music][voice]amix=inputs=2:duration=first:normalize=0[a]")
    elif audio_labels:
        filters.append(f"{audio_labels[0]}anull[a]")

    args = [*inputs, "-filter_complex", ";".join(filters), "-map", "[v]"]
    if audio_labels:
        args += ["-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-ar", "44100"]
    args += ["-t", f"{total:.3f}", "-c:v", "libx264", "-preset", profile.preset, "-crf", str(profile.crf),
             "-threads", str(settings.FFMPEG_THREADS), "-movflags", "+faststart", str(output)]
    ffmpeg(args, timeout=900)


def render_video(plan, *, profile, aspect, brand_color, logo_bytes=None, end_card_text="",
                 music_path=None, voice_path=None, voice_duration=None, progress=None):
    """Render the plan and return (mp4_bytes, info). Raises PlanError or FFmpegError.

    `plan` is a list of {"duration", "on_screen_text", "caption", "photo_bytes"}.
    """
    size = frame_size(aspect, profile)
    scenes = []
    for item in plan:
        scenes.append({
            "duration": item["duration"],
            "background": background_layer(size, brand_color, item.get("photo_bytes")),
            "text": text_layer(size, item.get("on_screen_text", ""), item.get("caption", "")),
        })
    if end_card_text or logo_bytes:
        scenes.append({
            "duration": 3,
            "background": end_card(size, brand_color, end_card_text, logo_bytes),
            "text": text_layer(size),
            "motion": False,
        })
    total = validate_plan(scenes, voice_duration)

    workdir = Path(tempfile.mkdtemp(prefix="jamii-render-"))
    try:
        clips = []
        for index, scene in enumerate(scenes):
            if progress:
                progress(f"Rendering scene {index + 1} of {len(scenes)}")
            clips.append(_render_scene(index, scene, size, profile, workdir))
        if progress:
            progress("Joining scenes and adding sound")
        output = workdir / "video.mp4"
        _join(clips, scenes, music_path, voice_path, output, profile, total)
        if progress:
            progress("Checking the finished video")
        problems = check_video(output, width=size[0], height=size[1], duration=total,
                               has_audio=bool(music_path or voice_path))
        if problems:
            raise FFmpegError("The finished video did not pass its checks: " + " ".join(problems))
        data = output.read_bytes()
        return data, {"width": size[0], "height": size[1], "duration": round(total, 2),
                      "scenes": len(scenes), "has_audio": bool(music_path or voice_path)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
