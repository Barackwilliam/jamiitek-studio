from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.projects.models import Project
from apps.website_analyzer.crawler import CrawledPage, CrawlResult
from apps.website_analyzer.extract import PageInfo
from apps.website_analyzer.jobs import (
    AnalysisAlreadyRunning,
    claim_next_analysis,
    fail_stale_analyses,
    request_analysis,
    run_analysis,
)
from apps.website_analyzer.models import AnalyzedPage, WebsiteAnalysis

START = "https://mamaneema.example/"


def fake_crawl(pages, stopped_reason=""):
    def crawl_function(start_url, *, max_pages, on_page, **kwargs):
        for page in pages:
            on_page(page)
        return CrawlResult(pages=list(pages), stopped_reason=stopped_reason)

    return crawl_function


def ok_page(url, title="Home"):
    info = PageInfo(title=title, text="Karibu", language="sw",
                    images=[{"url": url + "a.jpg", "alt": ""}],
                    structured_data=[{"@type": "LocalBusiness"}],
                    links=[{"url": url + "x", "text": "x"}])
    return CrawledPage(url=url, status="success", http_status=200, info=info)


class JobTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("neema", password="x-pass-123!")
        cls.other = User.objects.create_user("juma", password="x-pass-123!")
        cls.project = Project.objects.create(owner=cls.owner, name="Catering", website_url=START)
        cls.others_project = Project.objects.create(owner=cls.other, name="Tours",
                                                    website_url="https://tours.example/")


class RequestAndClaimTests(JobTestCase):
    def test_request_creates_queued_analysis(self):
        analysis = request_analysis(self.project)

        self.assertEqual(analysis.status, WebsiteAnalysis.Status.QUEUED)
        self.assertEqual(analysis.start_url, START)

    def test_second_request_while_active_is_refused(self):
        first = request_analysis(self.project)

        with self.assertRaises(AnalysisAlreadyRunning) as ctx:
            request_analysis(self.project)

        self.assertEqual(ctx.exception.analysis, first)
        self.assertEqual(self.project.analyses.count(), 1)

    def test_database_prevents_two_active_analyses(self):
        from django.db import IntegrityError, transaction

        WebsiteAnalysis.objects.create(project=self.project, start_url=START)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WebsiteAnalysis.objects.create(project=self.project, start_url=START)

    def test_new_request_allowed_after_completion(self):
        first = request_analysis(self.project)
        first.status = WebsiteAnalysis.Status.COMPLETED
        first.save()

        self.assertIsNotNone(request_analysis(self.project))

    def test_claim_takes_oldest_and_only_once(self):
        first = request_analysis(self.project)
        request_analysis(self.others_project)

        claimed = claim_next_analysis()

        self.assertEqual(claimed.pk, first.pk)
        self.assertEqual(claimed.status, WebsiteAnalysis.Status.RUNNING)
        self.assertIsNotNone(claimed.started_at)
        second = claim_next_analysis()
        self.assertNotEqual(second.pk, first.pk)
        self.assertIsNone(claim_next_analysis())

    def test_stale_running_analysis_is_failed(self):
        analysis = WebsiteAnalysis.objects.create(
            project=self.project, start_url=START, status=WebsiteAnalysis.Status.RUNNING,
            started_at=timezone.now() - timedelta(hours=1),
        )
        fresh = WebsiteAnalysis.objects.create(
            project=self.others_project, start_url=START, status=WebsiteAnalysis.Status.RUNNING,
            started_at=timezone.now(),
        )

        self.assertEqual(fail_stale_analyses(), 1)
        analysis.refresh_from_db()
        fresh.refresh_from_db()
        self.assertEqual(analysis.status, WebsiteAnalysis.Status.FAILED)
        self.assertEqual(analysis.error_code, "interrupted")
        self.assertEqual(fresh.status, WebsiteAnalysis.Status.RUNNING)


class RunAnalysisTests(JobTestCase):
    def setUp(self):
        self.analysis = request_analysis(self.project)
        claim_next_analysis()
        self.analysis.refresh_from_db()

    def test_successful_analysis_saves_pages(self):
        run_analysis(self.analysis, crawl_function=fake_crawl(
            [ok_page(START), ok_page(START + "about", "About")]))

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, WebsiteAnalysis.Status.COMPLETED)
        self.assertEqual((self.analysis.pages_succeeded, self.analysis.pages_attempted), (2, 2))
        first = self.analysis.pages.get(position=1)
        self.assertEqual(first.title, "Home")
        self.assertEqual(first.language, "sw")
        self.assertEqual(first.structured_types, ["LocalBusiness"])
        self.assertEqual(first.links_found, 1)

    def test_some_failed_pages_make_analysis_partial(self):
        failed = CrawledPage(url=START + "x", status="failed", error_code="timeout",
                             error_message="The website took too long to respond.")

        run_analysis(self.analysis, crawl_function=fake_crawl([ok_page(START), failed]))

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, WebsiteAnalysis.Status.PARTIAL)
        self.assertEqual(self.analysis.pages.get(position=2).error_code, "timeout")

    def test_skipped_pages_do_not_count_as_attempts(self):
        skipped = CrawledPage(url=START + "private", status="skipped", error_code="robots",
                              error_message="robots")

        run_analysis(self.analysis, crawl_function=fake_crawl([ok_page(START), skipped]))

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, WebsiteAnalysis.Status.COMPLETED)
        self.assertEqual(self.analysis.pages_attempted, 1)
        self.assertEqual(self.analysis.pages.count(), 2)

    def test_start_page_failure_fails_analysis_with_its_message(self):
        failed = CrawledPage(url=START, status="failed", error_code="dns_failed",
                             error_message="We could not find this website address.")

        run_analysis(self.analysis, crawl_function=fake_crawl([failed]))

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, WebsiteAnalysis.Status.FAILED)
        self.assertEqual(self.analysis.error_message, "We could not find this website address.")

    def test_crash_is_recorded_without_internal_details(self):
        def crashing_crawl(*args, **kwargs):
            raise RuntimeError("secret internal path /srv/app")

        with self.assertLogs("apps.website_analyzer.jobs", level="ERROR"):
            run_analysis(self.analysis, crawl_function=crashing_crawl)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, WebsiteAnalysis.Status.FAILED)
        self.assertEqual(self.analysis.error_code, "internal_error")
        self.assertNotIn("/srv", self.analysis.error_message)
        self.assertIsNotNone(self.analysis.finished_at)

    def test_stop_reason_is_saved(self):
        run_analysis(self.analysis, crawl_function=fake_crawl([ok_page(START)], "page_limit"))

        self.analysis.refresh_from_db()
        self.assertIn("limit of pages", self.analysis.stopped_message)


class WorkerCommandTests(JobTestCase):
    def test_once_processes_queue_and_exits(self):
        analysis = request_analysis(self.project)
        out = StringIO()

        with mock.patch("apps.website_analyzer.jobs.crawl", fake_crawl([ok_page(START)])):
            call_command("run_analysis_worker", "--once", stdout=out)

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, WebsiteAnalysis.Status.COMPLETED)
        self.assertIn("Finished website analysis", out.getvalue())

    def test_once_with_empty_queue_exits(self):
        out = StringIO()
        call_command("run_analysis_worker", "--once", stdout=out)
        self.assertIn("Worker started", out.getvalue())


class AnalysisViewTests(JobTestCase):
    def setUp(self):
        self.client.force_login(self.owner)

    def test_start_requires_post_and_login(self):
        url = reverse("website_analyzer:start", args=[self.project.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(WebsiteAnalysis.objects.exists())

    def test_start_queues_and_redirects_to_detail(self):
        response = self.client.post(reverse("website_analyzer:start", args=[self.project.pk]))

        analysis = self.project.analyses.get()
        self.assertRedirects(response, analysis.get_absolute_url())

    def test_double_start_does_not_duplicate(self):
        url = reverse("website_analyzer:start", args=[self.project.pk])
        self.client.post(url)
        response = self.client.post(url, follow=True)

        self.assertEqual(self.project.analyses.count(), 1)
        self.assertContains(response, "already in progress")

    def test_cannot_start_for_project_without_website(self):
        project = Project.objects.create(owner=self.owner, name="Manual", business_details="x")

        self.client.post(reverse("website_analyzer:start", args=[project.pk]))

        self.assertFalse(project.analyses.exists())

    def test_cannot_start_or_view_other_users_analysis(self):
        response = self.client.post(reverse("website_analyzer:start", args=[self.others_project.pk]))
        self.assertEqual(response.status_code, 404)

        other_analysis = request_analysis(self.others_project)
        url = reverse("website_analyzer:detail", args=[self.others_project.pk, other_analysis.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        # Wrong project id in the URL with the owner's own project also fails.
        url = reverse("website_analyzer:detail", args=[self.project.pk, other_analysis.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_active_analysis_page_refreshes_and_explains_status(self):
        analysis = request_analysis(self.project)

        response = self.client.get(analysis.get_absolute_url())

        self.assertContains(response, 'http-equiv="refresh"')
        self.assertContains(response, "Waiting for the analysis worker")

    def test_queued_too_long_hints_at_worker(self):
        analysis = request_analysis(self.project)
        WebsiteAnalysis.objects.filter(pk=analysis.pk).update(
            created_at=timezone.now() - timedelta(minutes=2))

        response = self.client.get(analysis.get_absolute_url())

        self.assertContains(response, "run_worker")

    def test_finished_analysis_shows_pages_escaped_and_no_refresh(self):
        analysis = request_analysis(self.project)
        claim_next_analysis()
        page = ok_page(START, title="<script>alert(1)</script>")
        run_analysis(analysis, crawl_function=fake_crawl([page]))

        response = self.client.get(analysis.get_absolute_url())

        self.assertNotContains(response, 'http-equiv="refresh"')
        self.assertContains(response, "1 of 1 pages analyzed successfully")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)")
        # Images from the website are listed as text, never loaded in the page.
        self.assertNotContains(response, f'<img src="{START}a.jpg"')

    def test_project_page_shows_analyze_button_and_latest_status(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "Analyze website")

        request_analysis(self.project)
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, "Waiting to start")
        self.assertNotContains(response, "Analyze again")

    def test_deleting_project_deletes_analyses(self):
        analysis = request_analysis(self.project)
        AnalyzedPage.objects.create(analysis=analysis, position=1, url=START, status="success")

        self.project.delete()

        self.assertFalse(WebsiteAnalysis.objects.exists())
        self.assertFalse(AnalyzedPage.objects.exists())
