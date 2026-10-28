import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.business_profiles.models import BusinessProfile, FactKey, ProfileFact
from apps.creative_assets.importing import candidate_images, request_import, run_import
from apps.creative_assets.models import Asset, ImageImportJob, Poster
from apps.marketing_content.models import ContentDraft, MarketingBrief
from apps.projects.models import Project
from apps.website_analyzer.fetch import FetchError, FetchResult
from apps.website_analyzer.models import AnalyzedPage, WebsiteAnalysis

from .helpers import image_bytes

SITE = "https://duka.example/"


class MediaTestCase(TestCase):
    """Each test gets its own temporary MEDIA_ROOT, so stored files never leak between tests."""

    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("asha", password="x-pass-123!")
        cls.other = User.objects.create_user("bakari", password="x-pass-123!")
        cls.project = Project.objects.create(owner=cls.owner, name="Duka", website_url=SITE)
        cls.other_project = Project.objects.create(owner=cls.other, name="Siri", business_details="x")
        analysis = WebsiteAnalysis.objects.create(project=cls.project, start_url=SITE,
                                                  status=WebsiteAnalysis.Status.COMPLETED)
        AnalyzedPage.objects.create(analysis=analysis, position=1, url=SITE, status="success", images=[
            {"url": SITE + "a.jpg", "alt": "Vitenge"}, {"url": SITE + "b.png", "alt": ""},
            {"url": SITE + "text.jpg", "alt": "not an image"}, {"url": SITE + "private/c.jpg", "alt": ""},
        ])
        profile = BusinessProfile.objects.create(project=cls.project)
        ProfileFact.objects.create(profile=profile, key=FactKey.LOGO, value=SITE + "logo.png", source="website")
        ProfileFact.objects.create(profile=profile, key=FactKey.PHONE, value="0754 123 456",
                                   source="website", status="confirmed")

    def stored_files(self):
        return [p for p in Path(self.media_root).rglob("*") if p.is_file()]


class FakeFetch:
    def __init__(self):
        self.calls = []
        self.bodies = {
            SITE + "a.jpg": ("image/jpeg", image_bytes("JPEG")),
            SITE + "b.png": ("image/png", image_bytes("PNG", color=(10, 20, 30))),
            SITE + "logo.png": ("image/png", image_bytes("PNG", size=(400, 200), mode="RGBA", color=(0, 90, 60, 255))),
            SITE + "text.jpg": ("image/jpeg", b"<html>not an image</html>"),
        }

    def __call__(self, url, **kwargs):
        self.calls.append(url)
        if url.endswith("robots.txt"):
            return FetchResult(url, 200, "text/plain", "utf-8", b"User-agent: *\nDisallow: /private/\n")
        if url not in self.bodies:
            raise FetchError("http_status", "missing")
        content_type, body = self.bodies[url]
        return FetchResult(url, 200, content_type, "", body)


class ImportTests(MediaTestCase):
    def test_candidates_include_logo_facts_first_and_page_images(self):
        urls = [c["url"] for c in candidate_images(self.project)]
        self.assertEqual(urls[0], SITE + "logo.png")
        self.assertIn(SITE + "a.jpg", urls)

    def test_only_candidates_can_be_requested(self):
        job = request_import(self.project, [SITE + "a.jpg", "http://169.254.169.254/x.png", SITE + "a.jpg"])
        self.assertEqual(job.urls, [SITE + "a.jpg"])
        with self.assertRaises(ValueError):
            request_import(self.other_project, ["https://evil.example/x.png"])

    def test_import_results(self):
        job = request_import(self.project, [SITE + "logo.png", SITE + "a.jpg", SITE + "text.jpg",
                                            SITE + "private/c.jpg", SITE + "b.png"])
        fetch = FakeFetch()

        job = run_import(job, fetch=fetch, sleep=lambda s: None)

        statuses = {r["url"]: r["status"] for r in job.results}
        self.assertEqual(statuses, {
            SITE + "logo.png": "imported", SITE + "a.jpg": "imported", SITE + "text.jpg": "failed",
            SITE + "private/c.jpg": "failed", SITE + "b.png": "imported",
        })
        self.assertNotIn(SITE + "private/c.jpg", fetch.calls)   # robots.txt honoured
        self.assertEqual(job.status, ImageImportJob.Status.COMPLETED)
        logo = Asset.objects.get(source_url=SITE + "logo.png")
        self.assertEqual((logo.kind, logo.origin, logo.rights_confirmed), ("logo", "website", True))
        self.assertEqual(Asset.objects.get(source_url=SITE + "a.jpg").alt_text, "Vitenge")

    def test_same_image_twice_is_a_duplicate(self):
        run_import(request_import(self.project, [SITE + "a.jpg"]), fetch=FakeFetch(), sleep=lambda s: None)
        job = run_import(request_import(self.project, [SITE + "a.jpg"]), fetch=FakeFetch(), sleep=lambda s: None)
        self.assertEqual(job.results[0]["status"], "duplicate")
        self.assertEqual(self.project.assets.count(), 1)


class LibraryViewTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def url(self, name, *args, project=None):
        return reverse(f"creative_assets:{name}", args=[(project or self.project).pk, *args])

    def upload(self, data=None, name="photo.jpg", rights="on", kind="image"):
        payload = {"image": SimpleUploadedFile(name, data or image_bytes("JPEG"), "image/jpeg"),
                   "kind": kind, "alt_text": "Duka letu"}
        if rights:
            payload["rights_confirmed"] = rights
        return self.client.post(self.url("upload"), payload, follow=True)

    def test_upload_stores_private_file_with_random_name(self):
        self.upload(name="../../etc/passwd.jpg")

        asset = self.project.assets.get()
        self.assertEqual((asset.origin, asset.original_name), ("upload", "passwd.jpg"))
        self.assertTrue(asset.file.name.startswith(f"projects/{self.project.pk}/assets/"))
        self.assertNotIn("passwd", asset.file.name)
        self.assertEqual(len(self.stored_files()), 2)   # image and thumbnail

    def test_upload_requires_rights_confirmation(self):
        response = self.upload(rights=None)
        self.assertContains(response, "This field is required")
        self.assertFalse(self.project.assets.exists())

    def test_fake_image_is_rejected(self):
        response = self.upload(data=b"<?php system($_GET['c']); ?>", name="shell.php.jpg")
        self.assertContains(response, "not a supported image")
        self.assertFalse(self.project.assets.exists())
        self.assertEqual(self.stored_files(), [])

    @override_settings(MAX_IMAGE_BYTES=1000)
    def test_oversized_upload_is_rejected(self):
        response = self.upload()
        self.assertContains(response, "larger than")

    def test_owner_can_view_file_with_safe_headers(self):
        self.upload()
        asset = self.project.assets.get()

        response = self.client.get(asset.thumbnail_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("private", response["Cache-Control"])
        b"".join(response.streaming_content)

    def test_other_users_cannot_reach_files_or_pages(self):
        self.upload()
        asset = self.project.assets.get()
        self.client.force_login(self.other)

        for method, url in [
            ("get", asset.file_url()), ("get", asset.thumbnail_url()), ("get", self.url("library")),
            ("get", self.url("import")), ("post", self.url("asset_delete", asset.pk)),
            ("post", self.url("upload")), ("get", self.url("poster_create")),
            # Own project id with someone else's asset id:
            ("get", reverse("creative_assets:asset_file", args=[self.other_project.pk, asset.pk, "full"])),
        ]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 404)
        self.assertTrue(Asset.objects.filter(pk=asset.pk).exists())

    def test_unknown_variant_is_not_routed(self):
        self.upload()
        asset = self.project.assets.get()
        response = self.client.get(f"/projects/{self.project.pk}/media/images/{asset.pk}/..%2f..%2fsettings/")
        self.assertEqual(response.status_code, 404)

    def test_deleting_asset_removes_its_files(self):
        self.upload()
        asset = self.project.assets.get()

        self.client.post(self.url("asset_delete", asset.pk))

        self.assertFalse(Asset.objects.exists())
        self.assertEqual(self.stored_files(), [])

    def test_deleting_project_removes_its_files(self):
        self.upload()
        self.project.delete()
        self.assertEqual(self.stored_files(), [])

    def test_import_page_lists_urls_without_loading_images(self):
        response = self.client.get(self.url("import"))
        self.assertContains(response, SITE + "a.jpg")
        self.assertNotContains(response, f'<img src="{SITE}')

    def test_import_requires_rights_confirmation(self):
        self.client.post(self.url("import"), {"urls": [SITE + "a.jpg"]})
        self.assertFalse(ImageImportJob.objects.exists())
        self.client.post(self.url("import"), {"urls": [SITE + "a.jpg"], "rights_confirmed": "on"})
        self.assertEqual(ImageImportJob.objects.get().urls, [SITE + "a.jpg"])


class PosterViewTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)
        self.url = reverse("creative_assets:poster_create", args=[self.project.pk])

    def make_script(self, status="approved"):
        brief = MarketingBrief.objects.create(project=self.project, objective="sales", audience="x",
                                              platform="instagram")
        return ContentDraft.objects.create(brief=brief, kind="script", status=status, data={
            "title": "Vitenge", "headline": "Vitenge vipya Arusha", "call_to_action": "Piga 0754 123 456"})

    def post(self, **data):
        payload = {"format": "square", "headline": "Karibu Duka", "subtext": "", "call_to_action": "",
                   "brand_color": "#0b6e4f"}
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_create_poster_and_download(self):
        response = self.post(format="portrait")

        poster = Poster.objects.get()
        self.assertRedirects(response, poster.get_absolute_url())
        self.assertEqual((poster.width, poster.height), (1080, 1920))
        download = self.client.get(poster.file_url() + "?download=1")
        self.assertIn("attachment", download["Content-Disposition"])
        b"".join(download.streaming_content)

    def test_approved_script_prefills_text(self):
        script = self.make_script()
        response = self.client.get(self.url + f"?script={script.pk}")
        self.assertContains(response, "Vitenge vipya Arusha")
        self.assertContains(response, "Piga 0754 123 456")

    def test_unapproved_script_is_ignored(self):
        script = self.make_script(status="generated")
        response = self.client.get(self.url + f"?script={script.pk}")
        self.assertNotContains(response, "Vitenge vipya Arusha")

    def test_unsupported_claims_are_flagged(self):
        self.post(headline="Bei nafuu zaidi Arusha", call_to_action="Punguzo 50% leo")

        flagged = {f["text"] for f in Poster.objects.get().flags}
        self.assertTrue({"bei nafuu zaidi", "punguzo", "50"} <= flagged)

    def test_confirmed_phone_is_not_flagged(self):
        self.post(call_to_action="Piga 0754 123 456")
        self.assertEqual(Poster.objects.get().flags, [])

    def test_other_users_asset_cannot_be_used(self):
        other_asset = Asset.objects.create(
            project=self.other_project, origin="upload", width=800, height=600, size_bytes=1,
            sha256="x" * 64, rights_confirmed=True, file="x.jpg", thumbnail="x.jpg")
        response = self.post(background=other_asset.pk)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Poster.objects.exists())

    def test_invalid_colour_is_rejected(self):
        response = self.post(brand_color="javascript:alert(1)")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Poster.objects.exists())

    def test_deleting_poster_removes_file(self):
        self.post()
        poster = Poster.objects.get()
        self.client.post(reverse("creative_assets:poster_delete", args=[self.project.pk, poster.pk]))
        self.assertEqual(self.stored_files(), [])
