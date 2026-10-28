import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.creative_assets.images import process_image
from apps.creative_assets.models import Asset
from apps.creative_assets.tests.helpers import image_bytes
from apps.marketing_content.models import ContentDraft, MarketingBrief
from apps.media_production.ffmpeg import FFmpegError, check_video
from apps.media_production.jobs import (
    RenderAlreadyRunning,
    build_plan,
    check_plan,
    claim_next_render,
    request_render,
    run_render,
)
from apps.media_production.models import AudioTrack, VideoRender
from apps.media_production.render import PlanError
from apps.projects.models import Project

from .helpers import make_audio, requires_ffmpeg, tiny_profiles

SCRIPT_DATA = {
    "title": "Harusi bila wasiwasi",
    "scenes": [
        {"voiceover": "Harusi inakaribia.", "on_screen_text": "Harusi?", "duration_seconds": 2},
        {"voiceover": "Tunapika kwa upendo.", "on_screen_text": "Mama Neema", "duration_seconds": 3},
        {"voiceover": "Tupigie leo.", "on_screen_text": "0712 345 678", "duration_seconds": 40},
    ],
    "call_to_action": "Piga 0712 345 678",
}


class VideoTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        media = override_settings(MEDIA_ROOT=self.media_root)
        media.enable()
        self.addCleanup(media.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("neema", password="x-pass-123!")
        cls.other = User.objects.create_user("juma", password="x-pass-123!")
        cls.project = Project.objects.create(owner=cls.owner, name="Mama Neema", business_details="x")
        cls.other_project = Project.objects.create(owner=cls.other, name="Siri", business_details="x")
        brief = MarketingBrief.objects.create(project=cls.project, objective="service", audience="x",
                                              platform="instagram")
        cls.script = ContentDraft.objects.create(brief=brief, kind="script", status="approved", data=SCRIPT_DATA)
        cls.draft = ContentDraft.objects.create(brief=brief, kind="script", status="generated", data=SCRIPT_DATA)

    def add_image(self, color=(200, 100, 50), kind="image"):
        return Asset.create_from_processed(
            project=self.project, processed=process_image(image_bytes("JPEG", color=color), 10**7),
            origin="upload", kind=kind, rights_confirmed=True)

    def stored_files(self):
        return [p for p in Path(self.media_root).rglob("*") if p.is_file()]


class PlanBuildingTests(VideoTestCase):
    def test_scenes_snapshot_with_images_in_order_and_clamped_durations(self):
        first, second = self.add_image(), self.add_image(color=(10, 20, 30))

        plan = build_plan(self.script, images=[first, second])

        self.assertEqual([s["image_id"] for s in plan["scenes"]], [first.pk, second.pk, first.pk])
        self.assertEqual([s["duration"] for s in plan["scenes"]], [2, 3, 15])
        self.assertEqual(plan["scenes"][0]["caption"], "Harusi inakaribia.")
        self.assertEqual(plan["end_card_text"], "Piga 0712 345 678")

    def test_options(self):
        plan = build_plan(self.script, images=[], captions=False, end_card=False)
        self.assertEqual({s["caption"] for s in plan["scenes"]}, {""})
        self.assertIsNone(plan["scenes"][0]["image_id"])
        self.assertEqual(plan["end_card_text"], "")

    def test_voiceover_longer_than_video_is_caught_before_queueing(self):
        plan = build_plan(self.script, images=[])
        voice = AudioTrack(duration=120)
        with self.assertRaises(PlanError):
            check_plan(plan, voice)

    def test_one_active_render_per_project(self):
        request_render(self.project, script=self.script, plan=build_plan(self.script, images=[]))
        with self.assertRaises(RenderAlreadyRunning):
            request_render(self.project, script=self.script, plan=build_plan(self.script, images=[]))


@requires_ffmpeg
class RunRenderTests(VideoTestCase):
    def test_end_to_end_render_is_validated_and_stored(self):
        image = self.add_image()
        self.add_image(color=(0, 90, 60), kind="logo")
        music = AudioTrack.create_from_processed(
            project=self.project, kind="music", rights_confirmed=True,
            processed=__import__("apps.media_production.audio", fromlist=["x"]).process_audio(make_audio(2)))
        script = ContentDraft.objects.get(pk=self.script.pk)
        script.data = {**SCRIPT_DATA, "scenes": SCRIPT_DATA["scenes"][:2]}
        plan = build_plan(script, images=[image])
        request_render(self.project, script=script, aspect="landscape", music=music, plan=plan)

        with tiny_profiles():
            video = run_render(claim_next_render())

        self.assertEqual(video.status, VideoRender.Status.COMPLETED, video.error_message)
        self.assertEqual((video.width, video.height, video.duration), (214, 120, 7.0))
        path = Path(self.media_root) / video.file.name
        self.assertEqual(check_video(path, width=214, height=120, duration=7.0, has_audio=True), [])
        # Only the stored files remain; temporary render folders are removed.
        self.assertFalse(list(Path(tempfile.gettempdir()).glob("jamiitek-tmp-*")))

    def test_deleted_image_falls_back_to_brand_colour(self):
        image = self.add_image()
        script = ContentDraft.objects.get(pk=self.script.pk)
        script.data = {**SCRIPT_DATA, "scenes": SCRIPT_DATA["scenes"][:1]}
        request_render(self.project, script=script, plan=build_plan(script, images=[image], end_card=False))
        image.delete()

        with tiny_profiles():
            video = run_render(claim_next_render())

        self.assertEqual(video.status, VideoRender.Status.COMPLETED)

    def test_ffmpeg_failure_is_recorded_without_details(self):
        request_render(self.project, script=self.script, plan=build_plan(self.script, images=[]))
        with mock.patch("apps.media_production.jobs.render_video",
                        side_effect=FFmpegError("Video processing failed.", "/secret/path stderr")):
            video = run_render(claim_next_render())

        self.assertEqual((video.status, video.error_code), ("failed", "ffmpeg"))
        self.assertNotIn("secret", video.error_message)
        self.assertFalse(video.file)


class VideoViewTests(VideoTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def url(self, name, *args, project=None):
        return reverse(f"media_production:{name}", args=[(project or self.project).pk, *args])

    def test_only_approved_scripts_can_be_used(self):
        form_page = self.client.get(self.url("create"))
        self.assertContains(form_page, "Harusi bila wasiwasi")

        response = self.client.post(self.url("create"), {
            "script": self.draft.pk, "aspect": "portrait", "quality": "preview", "captions": "on"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(VideoRender.objects.exists())

    def test_create_queues_render_with_snapshot(self):
        image = self.add_image()
        response = self.client.post(self.url("create"), {
            "script": self.script.pk, "aspect": "square", "quality": "preview",
            "images": [image.pk], "captions": "on", "end_card": "on"})

        video = VideoRender.objects.get()
        self.assertRedirects(response, video.get_absolute_url())
        self.assertEqual(video.plan["scenes"][0]["image_id"], image.pk)
        page = self.client.get(video.get_absolute_url())
        self.assertContains(page, 'http-equiv="refresh"')

    def test_other_users_images_cannot_be_chosen(self):
        other_image = Asset.objects.create(project=self.other_project, origin="upload", width=1, height=1,
                                           size_bytes=1, sha256="y" * 64, rights_confirmed=True)
        self.client.post(self.url("create"), {"script": self.script.pk, "aspect": "square",
                                              "quality": "preview", "images": [other_image.pk]})
        self.assertFalse(VideoRender.objects.exists())

    def test_unfinished_video_file_is_not_served(self):
        video = request_render(self.project, script=self.script, plan=build_plan(self.script, images=[]))
        self.assertEqual(self.client.get(self.url("video_file", video.pk)).status_code, 404)
        self.client.post(self.url("video_delete", video.pk))
        self.assertTrue(VideoRender.objects.filter(pk=video.pk).exists())

    def test_other_users_cannot_reach_videos_or_audio(self):
        video = request_render(self.project, script=self.script, plan=build_plan(self.script, images=[]))
        track = AudioTrack.objects.create(project=self.project, kind="music", duration=2, size_bytes=1,
                                          sha256="z" * 64, rights_confirmed=True, file="a.m4a")
        self.client.force_login(self.other)
        for method, url in [
            ("get", self.url("videos")), ("get", self.url("create")), ("get", video.get_absolute_url()),
            ("get", self.url("video_file", video.pk)), ("post", self.url("video_delete", video.pk)),
            ("get", self.url("audio_file", track.pk)), ("post", self.url("audio_delete", track.pk)),
            ("post", self.url("upload_audio")),
            ("get", reverse("media_production:video", args=[self.other_project.pk, video.pk])),
        ]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 404)

    @requires_ffmpeg
    def test_audio_upload_validation_and_cleanup(self):
        response = self.client.post(self.url("upload_audio"), {
            "audio": SimpleUploadedFile("song.mp3", image_bytes("PNG")), "kind": "music",
            "rights_confirmed": "on"}, follow=True)
        self.assertContains(response, "Please upload MP3, M4A, WAV or OGG audio.")
        self.assertFalse(AudioTrack.objects.exists())

        self.client.post(self.url("upload_audio"), {
            "audio": SimpleUploadedFile("voice.m4a", make_audio(2)), "kind": "voiceover"})
        self.assertFalse(AudioTrack.objects.exists())   # rights not confirmed

        self.client.post(self.url("upload_audio"), {
            "audio": SimpleUploadedFile("voice.m4a", make_audio(2)), "kind": "voiceover",
            "rights_confirmed": "on"})
        track = AudioTrack.objects.get()
        self.assertEqual(track.kind, "voiceover")
        self.assertEqual(len(self.stored_files()), 1)

        self.client.post(self.url("audio_delete", track.pk))
        self.assertEqual(self.stored_files(), [])

    @override_settings(FFMPEG_PATH="/nonexistent/ffmpeg")
    def test_missing_ffmpeg_is_explained(self):
        response = self.client.get(self.url("videos"))
        self.assertContains(response, "FFmpeg is not installed")
