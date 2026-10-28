import os
import shutil
import tempfile
import time
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.models import RateLimitEvent, WorkerHeartbeat
from apps.core.worker import JobHandler
from apps.creative_assets.images import process_image
from apps.creative_assets.models import Asset
from apps.creative_assets.tests.helpers import image_bytes
from apps.marketing_content.models import ContentDraft, DraftRevision, MarketingBrief
from apps.media_production.models import VideoRender
from apps.projects.models import Project

PASSWORD = "Correct-horse-9"


class TempMediaMixin:
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        media = override_settings(MEDIA_ROOT=self.media_root)
        media.enable()
        self.addCleanup(media.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)


class LoginRateLimitTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("juma", password=PASSWORD)

    def login(self, username="juma", password="wrong", ip="10.0.0.1"):
        return self.client.post(reverse("login"), {"username": username, "password": password},
                                REMOTE_ADDR=ip)

    def test_locks_after_five_failures_even_with_the_right_password(self):
        for _ in range(5):
            self.login()

        response = self.login(password=PASSWORD)

        self.assertContains(response, "Too many failed attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_message_is_the_same_for_unknown_usernames(self):
        for _ in range(5):
            self.login(username="nobody")
        self.assertContains(self.login(username="nobody"), "Too many failed attempts")

    def test_other_usernames_are_not_locked_by_one_users_failures(self):
        get_user_model().objects.create_user("asha", password=PASSWORD)
        for _ in range(5):
            self.login(ip="10.0.0.9")
        response = self.login(username="asha", password=PASSWORD, ip="10.0.0.9")
        self.assertRedirects(response, reverse("projects:list"))

    def test_one_address_trying_many_usernames_is_limited(self):
        for i in range(20):
            self.login(username=f"user{i}", ip="10.0.0.5")
        response = self.login(password=PASSWORD, ip="10.0.0.5")
        self.assertContains(response, "Too many failed attempts")

    def test_success_clears_earlier_failures(self):
        for _ in range(4):
            self.login()
        self.assertRedirects(self.login(password=PASSWORD), reverse("projects:list"))
        self.client.logout()
        for _ in range(4):
            self.login()
        self.assertRedirects(self.login(password=PASSWORD), reverse("projects:list"))

    def test_lock_expires_after_the_window(self):
        for _ in range(5):
            self.login()
        RateLimitEvent.objects.update(created_at=timezone.now() - timedelta(minutes=16))
        self.assertRedirects(self.login(password=PASSWORD), reverse("projects:list"))

    def test_only_hashes_are_stored(self):
        self.login(ip="198.51.100.7")
        stored = " ".join(RateLimitEvent.objects.values_list("key_hash", flat=True))
        self.assertNotIn("juma", stored)
        self.assertNotIn("198.51.100.7", stored)


class SignupRateLimitTests(TestCase):
    def test_signups_per_address_are_limited(self):
        for i in range(10):
            self.client.post(reverse("signup"), {"username": f"u{i}", "password1": "x", "password2": "y"},
                             REMOTE_ADDR="10.1.1.1")
        response = self.client.post(reverse("signup"), {
            "username": "late", "password1": PASSWORD, "password2": PASSWORD}, REMOTE_ADDR="10.1.1.1")
        self.assertEqual(response.status_code, 429)
        self.assertFalse(get_user_model().objects.filter(username="late").exists())


class SecurityHeaderTests(TestCase):
    def test_pages_send_a_strict_content_security_policy(self):
        response = self.client.get(reverse("core:home"))
        csp = response["Content-Security-Policy"]
        for directive in ["default-src 'self'", "script-src 'self'", "object-src 'none'",
                          "frame-ancestors 'none'", "form-action 'self'"]:
            self.assertIn(directive, csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertIn("camera=()", response["Permissions-Policy"])


class RangeRequestTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("neema", password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, name="P", business_details="x")
        self.asset = Asset.create_from_processed(
            project=self.project, processed=process_image(image_bytes("JPEG"), 10**7),
            origin="upload", rights_confirmed=True)
        self.content = self.asset.file.open("rb").read()
        self.asset.file.close()
        self.url = self.asset.file_url()
        self.client.force_login(self.user)

    def get(self, range_header=None):
        headers = {"HTTP_RANGE": range_header} if range_header else {}
        response = self.client.get(self.url, **headers)
        body = b"".join(response.streaming_content) if response.streaming else response.content
        return response, body

    def test_full_file_advertises_ranges(self):
        response, body = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(body, self.content)

    def test_ranges(self):
        size = len(self.content)
        for header, start, end in [("bytes=0-9", 0, 9), ("bytes=10-", 10, size - 1),
                                   ("bytes=-5", size - 5, size - 1), (f"bytes=5-{size + 100}", 5, size - 1)]:
            with self.subTest(header=header):
                response, body = self.get(header)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response["Content-Range"], f"bytes {start}-{end}/{size}")
                self.assertEqual(body, self.content[start:end + 1])

    def test_unsatisfiable_and_unsupported_ranges(self):
        size = len(self.content)
        response, _ = self.get(f"bytes={size}-")
        self.assertEqual(response.status_code, 416)
        self.assertEqual(response["Content-Range"], f"bytes */{size}")
        response, body = self.get("bytes=0-1,5-6")      # multiple ranges: whole file
        self.assertEqual((response.status_code, body), (200, self.content))

    def test_ranges_still_require_ownership(self):
        self.client.force_login(get_user_model().objects.create_user("other", password=PASSWORD))
        self.assertEqual(self.client.get(self.url, HTTP_RANGE="bytes=0-9").status_code, 404)


class WorkerRobustnessTests(TestCase):
    def test_a_failing_handler_does_not_stop_the_worker(self):
        calls = []

        def broken_claim():
            raise RuntimeError("database hiccup")

        def good_claim():
            calls.append("claimed")
            return None

        fake = [JobHandler("broken", broken_claim, None, lambda: 0, str),
                JobHandler("good", good_claim, None, lambda: 0, str)]
        out, err = StringIO(), StringIO()
        with mock.patch("apps.core.management.commands.run_worker.handlers", return_value=fake), \
                self.assertLogs("apps.core.management.commands.run_worker", "ERROR"):
            call_command("run_worker", "--once", stdout=out, stderr=err)

        self.assertEqual(calls, ["claimed"])
        self.assertIn("Error in broken", err.getvalue())
        self.assertIsNotNone(WorkerHeartbeat.objects.get().last_error_at)

    def test_health_reports_worker_state(self):
        self.assertEqual(self.client.get(reverse("core:health")).json()["checks"]["worker"], "not_seen")
        call_command("run_worker", "--once", stdout=StringIO())
        self.assertEqual(self.client.get(reverse("core:health")).json()["checks"]["worker"], "ok")
        WorkerHeartbeat.objects.update(last_seen=timezone.now() - timedelta(minutes=5))
        self.assertEqual(self.client.get(reverse("core:health")).json()["checks"]["worker"], "stale")


class ScriptRevisionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("neema", password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, name="P", business_details="x")
        brief = MarketingBrief.objects.create(project=self.project, objective="sales", audience="x",
                                              platform="instagram")
        self.script = ContentDraft.objects.create(
            brief=brief, kind="script", status="approved", approved_at=timezone.now(),
            data={"title": "Original", "headline": "", "caption": "", "call_to_action": "", "hashtags": [],
                  "scenes": [{"voiceover": "Karibu", "on_screen_text": "", "visual": "", "duration_seconds": 5,
                              "fact_ids": []}]})
        self.client.force_login(self.user)

    def edit(self, title, caption=""):
        return self.client.post(reverse("marketing_content:script_edit", args=[self.project.pk, self.script.pk]), {
            "title": title, "headline": "", "caption": caption, "call_to_action": "", "hashtags": "",
            "scenes-TOTAL_FORMS": 1, "scenes-INITIAL_FORMS": 1, "scenes-MIN_NUM_FORMS": 1,
            "scenes-MAX_NUM_FORMS": 10, "scenes-0-voiceover": "Karibu", "scenes-0-on_screen_text": "",
            "scenes-0-visual": "", "scenes-0-duration_seconds": 5})

    def test_editing_keeps_the_previous_version_and_restore_needs_new_approval(self):
        self.edit("Changed", caption="Bora zaidi mjini")
        revision = self.script.revisions.get()
        self.assertEqual((revision.data["title"], revision.status), ("Original", "approved"))

        self.edit("Changed again")
        self.client.post(reverse("marketing_content:script_restore",
                                 args=[self.project.pk, self.script.pk, revision.pk]))

        self.script.refresh_from_db()
        self.assertEqual(self.script.data["title"], "Original")
        self.assertEqual(self.script.status, "edited")
        self.assertIsNone(self.script.approved_at)
        self.assertEqual(self.script.revisions.count(), 3)

    def test_history_is_capped(self):
        for i in range(DraftRevision.MAX_PER_DRAFT + 5):
            self.edit(f"Version {i}")
        self.assertEqual(self.script.revisions.count(), DraftRevision.MAX_PER_DRAFT)

    def test_other_users_cannot_restore(self):
        self.edit("Changed")
        revision = self.script.revisions.get()
        self.client.force_login(get_user_model().objects.create_user("x", password=PASSWORD))
        response = self.client.post(reverse("marketing_content:script_restore",
                                            args=[self.project.pk, self.script.pk, revision.pk]))
        self.assertEqual(response.status_code, 404)


class VideoRetryTests(TestCase):
    def test_failed_video_can_be_retried_with_the_same_settings(self):
        user = get_user_model().objects.create_user("neema", password=PASSWORD)
        project = Project.objects.create(owner=user, name="P", business_details="x")
        plan = {"scenes": [{"duration": 4, "on_screen_text": "", "caption": "", "image_id": None}],
                "end_card": False, "end_card_text": ""}
        failed = VideoRender.objects.create(project=project, aspect="square", quality="final", plan=plan,
                                            status="failed", error_message="x")
        self.client.force_login(user)

        response = self.client.post(reverse("media_production:video_retry", args=[project.pk, failed.pk]))

        retry = VideoRender.objects.exclude(pk=failed.pk).get()
        self.assertRedirects(response, retry.get_absolute_url())
        self.assertEqual((retry.status, retry.aspect, retry.quality, retry.plan), ("queued", "square", "final", plan))
        self.assertEqual(self.client.post(reverse("media_production:video_retry",
                                                  args=[project.pk, retry.pk])).status_code, 404)


class CleanupTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_user("neema", password=PASSWORD)
        project = Project.objects.create(owner=user, name="P", business_details="x")
        self.asset = Asset.create_from_processed(
            project=project, processed=process_image(image_bytes("JPEG"), 10**7),
            origin="upload", rights_confirmed=True)
        self.orphan = Path(self.media_root) / "projects" / str(project.pk) / "assets" / "leftover.jpg"
        self.orphan.write_bytes(b"old file")
        self.recent = self.orphan.with_name("new.jpg")
        self.recent.write_bytes(b"being written")
        old = time.time() - 2 * 3600
        os.utime(self.orphan, (old, old))
        self.temp_old = Path(tempfile.mkdtemp(prefix="jamiitek-tmp-test-"))
        os.utime(self.temp_old, (time.time() - 7 * 3600,) * 2)
        self.unrelated = Path(tempfile.mkdtemp(prefix="jamii-unrelated-"))
        os.utime(self.unrelated, (time.time() - 7 * 3600,) * 2)
        self.addCleanup(shutil.rmtree, self.temp_old, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.unrelated, ignore_errors=True)

    def test_dry_run_deletes_nothing(self):
        out = StringIO()
        call_command("cleanup", stdout=out)
        self.assertIn("leftover.jpg", out.getvalue())
        self.assertNotIn("new.jpg", out.getvalue())
        self.assertTrue(self.orphan.exists() and self.temp_old.exists())

    def test_delete_removes_only_old_orphans_and_own_temp_folders(self):
        call_command("cleanup", "--delete", stdout=StringIO())

        self.assertFalse(self.orphan.exists())
        self.assertTrue(self.recent.exists())                       # may be in use
        self.assertTrue(Path(self.media_root, self.asset.file.name).exists())
        self.assertTrue(Path(self.media_root, self.asset.thumbnail.name).exists())
        self.assertFalse(self.temp_old.exists())
        self.assertTrue(self.unrelated.exists())                    # not ours
