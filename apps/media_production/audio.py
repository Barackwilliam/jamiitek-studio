"""Validating and normalizing uploaded music and voice-over recordings.

The file's name and declared type are not trusted: FFprobe must find an
audio stream in an accepted container, the length is limited, and the audio
is re-encoded to AAC without metadata (cover art and tags are dropped).
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from .ffmpeg import FFmpegError, duration_of, ffmpeg, probe, streams

ACCEPTED_CONTAINERS = {"mp3", "mov", "mp4", "m4a", "3gp", "3g2", "mj2", "wav", "ogg", "matroska", "webm", "aac"}
MIN_SECONDS = 1
MAX_SECONDS = 600


class InvalidAudio(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ProcessedAudio:
    content: bytes
    duration: float


def process_audio(data):
    with tempfile.TemporaryDirectory(prefix="jamii-audio-") as folder:
        source = Path(folder) / "input"
        output = Path(folder) / "audio.m4a"
        source.write_bytes(data)
        try:
            info = probe(source)
        except FFmpegError:
            raise InvalidAudio("This file is not a supported audio file.")
        container = set(info.get("format", {}).get("format_name", "").split(","))
        if not container & ACCEPTED_CONTAINERS:
            raise InvalidAudio("Please upload MP3, M4A, WAV or OGG audio.")
        if not streams(info, "audio"):
            raise InvalidAudio("The file has no sound.")
        duration = duration_of(info)
        if not MIN_SECONDS <= duration <= MAX_SECONDS:
            raise InvalidAudio(f"Audio must last between {MIN_SECONDS} second and {MAX_SECONDS // 60} minutes.")
        try:
            ffmpeg(["-i", str(source), "-map", "0:a:0", "-vn", "-map_metadata", "-1",
                    "-ac", "2", "-ar", "44100", "-c:a", "aac", "-b:a", "128k", str(output)], timeout=180)
            return ProcessedAudio(content=output.read_bytes(), duration=round(duration_of(probe(output)), 2))
        except FFmpegError:
            raise InvalidAudio("The audio could not be processed. It may be damaged.")
