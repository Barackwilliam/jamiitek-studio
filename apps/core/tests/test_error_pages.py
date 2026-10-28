from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.views.defaults import server_error

from apps.projects.models import Project


class ErrorPageTests(TestCase):
    def test_404_is_friendly_and_does_not_leak_details(self):
        response = self.client.get("/hakuna-ukurasa/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Page not found", status_code=404)
        self.assertNotContains(response, "urlpatterns", status_code=404)

    def test_another_users_project_looks_like_a_missing_page(self):
        User = get_user_model()
        owner = User.objects.create_user("amina", password="test-pass-123!")
        other = User.objects.create_user("baraka", password="test-pass-123!")
        project = Project.objects.create(owner=owner, name="Duka", business_details="x")
        self.client.force_login(other)
        response = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertContains(response, "belongs to another account", status_code=404)
        self.assertNotContains(response, "Duka", status_code=404)

    def test_500_page_renders_without_request_context(self):
        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Something went wrong", response.content)
        self.assertIn(b"Your saved work is safe", response.content)

    def test_csrf_failure_explains_what_to_do(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("login"), {"username": "a", "password": "b"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Please try again", status_code=403)
        self.assertContains(response, "reload the page", status_code=403)

    @override_settings(LANGUAGE_CODE="sw")
    def test_error_pages_follow_the_language(self):
        response = self.client.get("/hakuna-ukurasa/", HTTP_ACCEPT_LANGUAGE="sw")
        self.assertContains(response, '<html lang="sw">', status_code=404)
