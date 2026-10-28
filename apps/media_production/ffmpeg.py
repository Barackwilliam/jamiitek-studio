"""Running FFmpeg and FFprobe safely, and checking their output.

Commands are always argument lists (never a shell), have a timeout, and
never contain user text: all text is drawn into images beforehand.
"""

import json
import logging
import subprocess

from django.conf import settings
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """`message` is safe to show users; details are logged."""

    def __init__(self, message, detail=""):
        super().__init__(message)
        self.message = str(message)  # translated in the active language
        self.detail = detail


def _run(args, timeout):
    try:
        result = subprocess.run(args, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise FFmpegError(_("FFmpeg is not installed or could not be found. See README.")) from exc
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(_("Video processing took too long and was stopped.")) from exc
    return result


def ffmpeg(args, timeout=600):
    """Run ffmpeg with the given arguments (without the program name)."""
    command = [settings.FFMPEG_PATH, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", *args]
    result = _run(command, timeout)
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace")[-2000:]
        logger.error("ffmpeg failed (%s): %s", result.returncode, detail)
        raise FFmpegError(_("Video processing failed."), detail)
    return result


def probe(path, timeout=60):
    """Return ffprobe's description of a media file as a dict."""
    command = [settings.FFPROBE_PATH, "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(path)]
    result = _run(command, timeout)
    if result.returncode != 0:
        raise FFmpegError(_("The file is not a readable media file."),
                          result.stderr.decode(errors="replace")[-2000:])
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise FFmpegError(_("The file is not a readable media file.")) from exc


def tools_available():
    try:
        return _run([settings.FFMPEG_PATH, "-version"], 15).returncode == 0 and \
            _run([settings.FFPROBE_PATH, "-version"], 15).returncode == 0
    except FFmpegError:
        return False


def streams(info, kind):
    return [s for s in info.get("streams", []) if s.get("codec_type") == kind]


def duration_of(info):
    try:
        return float(info["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def check_video(path, *, width, height, duration, has_audio, tolerance=0.6):
    """Return a list of problems with a rendered MP4 (empty when it is valid).

    Checks the container, the H.264 video stream, its size and pixel format,
    the duration, the audio stream when one is expected, and that every
    frame decodes without errors.
    """
    problems = []
    try:
        info = probe(path)
    except FFmpegError as exc:
        return [exc.message]
    if "mp4" not in info.get("format", {}).get("format_name", ""):
        problems.append("The file is not an MP4 container.")
    videos = streams(info, "video")
    if len(videos) != 1:
        problems.append("The file does not have exactly one video stream.")
    else:
        video = videos[0]
        if video.get("codec_name") != "h264":
            problems.append("The video is not H.264.")
        if (video.get("width"), video.get("height")) != (width, height):
            problems.append(f"The video is {video.get('width')}×{video.get('height')}, expected {width}×{height}.")
        if video.get("pix_fmt") != "yuv420p":
            problems.append("The video uses a pixel format many players cannot show.")
    actual = duration_of(info)
    if abs(actual - duration) > tolerance:
        problems.append(f"The video lasts {actual:.1f} s, expected {duration:.1f} s.")
    audios = streams(info, "audio")
    if has_audio and not audios:
        problems.append("The video has no sound, but sound was expected.")
    if not has_audio and audios:
        problems.append("The video has an unexpected sound track.")
    if not problems:
        decode = _run([settings.FFMPEG_PATH, "-hide_banner", "-nostdin", "-v", "error",
                       "-i", str(path), "-f", "null", "-"], 300)
        if decode.returncode != 0 or decode.stderr.strip():
            problems.append("The video could not be decoded completely.")
    return problems
