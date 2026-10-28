import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from apps.creative_assets.tests.helpers import image_bytes
from apps.media_production.audio import InvalidAudio, process_audio
from apps.media_production.ffmpeg import FFmpegError, check_video, probe, streams, tools_available
from apps.media_production.render import (
    PROFILES,
    PlanError,
    frame_size,
    render_video,
    total_duration,
    validate_plan,
)

from .helpers import TEST_PROFILE, make_audio, requires_ffmpeg


def scene(duration=2, **extra):
    return {"duration": duration, "on_screen_text": "Karibu", "caption": "Tunapika kwa upendo", **extra}


class PlanTests(SimpleTestCase):
    def test_frame_sizes_are_even_and_match_aspect(self):
        self.assertEqual(frame_size("portrait", PROFILES["final"]), (1080, 1920))
        self.assertEqual(frame_size("landscape", PROFILES["preview"]), (960, 540))
        self.assertEqual(frame_size("square", PROFILES["preview"]), (540, 540))
        for aspect in ("portrait", "square", "landscape"):
            self.assertTrue(all(side % 2 == 0 for side in frame_size(aspect, TEST_PROFILE)))

    def test_total_duration_accounts_for_crossfades(self):
        self.assertEqual(total_duration([scene(4), scene(5), scene(3)]), 11.0)

    def test_invalid_plans(self):
        cases = [
            ([], "no scenes"),
            ([scene(1)], "between"),
            ([scene(16)], "between"),
            ([scene(15)] * 10, "limit"),
        ]
        for scenes, text in cases:
            with self.subTest(text=text), self.assertRaises(PlanError) as ctx:
                validate_plan(scenes)
            self.assertIn(text, ctx.exception.message)

    def test_voiceover_longer_than_video_is_refused(self):
        with self.assertRaises(PlanError) as ctx:
            validate_plan([scene(5), scene(5)], voice_duration=20)
        self.assertIn("voice-over", ctx.exception.message)
        self.assertEqual(validate_plan([scene(5), scene(5)], voice_duration=9), 9.5)


@requires_ffmpeg
class RenderTests(SimpleTestCase):
    def render(self, plan, **kwargs):
        options = {"profile": TEST_PROFILE, "aspect": "portrait", "brand_color": "#0b6e4f"}
        options.update(kwargs)
        return render_video(plan, **options)

    def save(self, data):
        folder = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        path = Path(folder) / "video.mp4"
        path.write_bytes(data)
        return path

    def test_renders_valid_video_without_sound(self):
        steps = []
        data, info = self.render(
            [scene(2, photo_bytes=image_bytes("JPEG")), scene(3)],
            logo_bytes=image_bytes("PNG", size=(300, 120), mode="RGBA", color=(0, 90, 60, 255)),
            end_card_text="Piga 0712 345 678", progress=steps.append,
        )

        self.assertEqual(info, {"width": 120, "height": 214, "duration": 7.0, "scenes": 3, "has_audio": False})
        path = self.save(data)
        self.assertEqual(check_video(path, width=120, height=214, duration=7.0, has_audio=False), [])
        self.assertEqual(steps[0], "Rendering scene 1 of 3")
        self.assertEqual(steps[-1], "Checking the finished video")

    def test_music_and_voiceover_are_mixed(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        music, voice = folder / "music.m4a", folder / "voice.m4a"
        music.write_bytes(make_audio(2))          # shorter than the video: must loop
        voice.write_bytes(make_audio(3))

        data, info = self.render([scene(3), scene(3)], aspect="square",
                                 music_path=music, voice_path=voice, voice_duration=3)

        path = self.save(data)
        self.assertTrue(info["has_audio"])
        self.assertEqual(check_video(path, width=120, height=120, duration=5.5, has_audio=True), [])

    def test_hostile_text_never_reaches_ffmpeg(self):
        text = "'; rm -rf / \"$(reboot)\" `id` %{pts} :drawtext=x"
        data, _ = self.render([scene(2, on_screen_text=text, caption=text)])
        self.assertTrue(data.startswith(b"\x00\x00\x00") or b"ftyp" in data[:32])

    def test_checks_detect_broken_or_wrong_videos(self):
        data, _ = self.render([scene(2)])
        path = self.save(data)
        self.assertIn("expected 200×200", " ".join(check_video(path, width=200, height=200, duration=2, has_audio=False)))
        self.assertIn("no sound", " ".join(check_video(path, width=120, height=214, duration=2, has_audio=True)))
        self.assertIn("lasts", " ".join(check_video(path, width=120, height=214, duration=9, has_audio=False)))

        broken = self.save(data[: len(data) // 2])
        self.assertTrue(check_video(broken, width=120, height=214, duration=2, has_audio=False))
        not_video = self.save(b"plain text, not a video")
        self.assertTrue(check_video(not_video, width=120, height=214, duration=2, has_audio=False))

    @override_settings(FFMPEG_PATH="/nonexistent/ffmpeg", FFPROBE_PATH="/nonexistent/ffprobe")
    def test_missing_ffmpeg_is_reported_clearly(self):
        self.assertFalse(tools_available())
        with self.assertRaises(FFmpegError) as ctx:
            self.render([scene(2)])
        self.assertIn("not installed", ctx.exception.message)


@requires_ffmpeg
class AudioTests(SimpleTestCase):
    def test_common_formats_are_normalized_without_metadata(self):
        for codec, extension in [("aac", "m4a"), ("pcm_s16le", "wav"), ("libvorbis", "ogg")]:
            with self.subTest(extension=extension):
                processed = process_audio(make_audio(2, codec=codec, extension=extension, title="Secret Title"))
                self.assertAlmostEqual(processed.duration, 2.0, delta=0.2)
                self.assertNotIn(b"Secret Title", processed.content)
                folder = Path(tempfile.mkdtemp())
                (folder / "a.m4a").write_bytes(processed.content)
                info = probe(folder / "a.m4a")
                self.assertEqual(streams(info, "audio")[0]["codec_name"], "aac")
                self.assertEqual(streams(info, "video"), [])

    def test_rejected_files(self):
        cases = {
            "image": image_bytes("PNG"),
            "text": b"not audio at all",
            "too long": make_audio(601, codec="pcm_s16le", extension="wav", rate=8000),
            "too short": make_audio(0.5),
        }
        for name, data in cases.items():
            with self.subTest(name), self.assertRaises(InvalidAudio):
                process_audio(data)
