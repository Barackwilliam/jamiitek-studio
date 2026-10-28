import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apps.media_production import render
from apps.media_production.ffmpeg import tools_available

# A tiny, fast profile so tests render real videos in a second or two.
TEST_PROFILE = render.Profile("test", 120, 10, 32, "ultrafast")

requires_ffmpeg = unittest.skipUnless(tools_available(), "Blocked: FFmpeg is not installed")


def tiny_profiles():
    return mock.patch.dict(render.PROFILES, {"preview": TEST_PROFILE, "final": TEST_PROFILE})


def make_audio(seconds, *, codec="aac", extension="m4a", rate=22050, title=None):
    """Generate a test tone with FFmpeg and return its bytes."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"tone.{extension}"
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                "-i", f"sine=frequency=440:sample_rate={rate}:duration={seconds}", "-c:a", codec]
        if title:
            args += ["-metadata", f"title={title}"]
        subprocess.run([*args, str(path)], check=True)
        return path.read_bytes()
