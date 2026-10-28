from unittest import mock

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "JamiiTek")

    def test_home_page_states_development_status_honestly(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Website analysis and content creation are not available yet")
        self.assertNotContains(response, "<form")

    def test_home_page_declares_language_and_skip_link(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, 'href="#main"')

    def test_home_page_rejects_post(self):
        response = self.client.post(reverse("core:home"))

        self.assertEqual(response.status_code, 405)


class HealthCheckTests(TestCase):
    def test_health_reports_ok_when_database_available(self):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "ok", "checks": {"database": "ok", "worker": "not_seen"}}
        )

    def test_health_is_not_cached(self):
        response = self.client.get(reverse("core:health"))

        self.assertIn("no-store", response["Cache-Control"])

    def test_health_reports_error_without_details_when_database_fails(self):
        secret_detail = "could not open database file /private/path/db.sqlite3"
        with mock.patch(
            "apps.core.views.connection.cursor",
            side_effect=OperationalError(secret_detail),
        ), self.assertLogs("apps.core.views", level="ERROR"):
            response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"status": "error", "checks": {"database": "error"}}
        )
        self.assertNotIn("private", response.content.decode())

    def test_health_rejects_post(self):
        response = self.client.post(reverse("core:health"))

        self.assertEqual(response.status_code, 405)

    def test_health_supports_head(self):
        response = self.client.head(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
