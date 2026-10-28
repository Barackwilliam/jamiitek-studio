from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Project
from apps.website_analyzer.url_safety import UnsafeURLError

PUBLIC_IP = "93.184.215.14"


def public_resolver(hostname, port):
    return [PUBLIC_IP]


class ProjectTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("amina", password="test-pass-123!")
        cls.other = User.objects.create_user("baraka", password="test-pass-123!")
        cls.project = Project.objects.create(
            owner=cls.owner,
            name="Duka la Amina",
            business_name="Amina Fashion",
            website_url="https://amina.example/",
        )
        cls.others_project = Project.objects.create(
            owner=cls.other, name="Baraka Tours", business_details="Safari tours in Arusha."
        )

    def setUp(self):
        self.client.force_login(self.owner)
        # No test in this module may perform real DNS lookups.
        patcher = mock.patch(
            "apps.website_analyzer.url_safety.resolve_host", side_effect=public_resolver
        )
        self.resolver = patcher.start()
        self.addCleanup(patcher.stop)


class LoginRequiredTests(ProjectTestCase):
    def test_all_project_pages_require_login(self):
        self.client.logout()
        urls = [
            reverse("projects:list"),
            reverse("projects:create"),
            reverse("projects:detail", args=[self.project.pk]),
            reverse("projects:update", args=[self.project.pk]),
            reverse("projects:delete", args=[self.project.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")


class ProjectListTests(ProjectTestCase):
    def test_lists_only_own_projects(self):
        response = self.client.get(reverse("projects:list"))

        self.assertContains(response, "Duka la Amina")
        self.assertNotContains(response, "Baraka Tours")

    def test_empty_state_guides_new_users(self):
        self.client.force_login(get_user_model().objects.create_user("new", password="x-pass-123!"))

        response = self.client.get(reverse("projects:list"))

        self.assertContains(response, "You have no projects yet.")
        self.assertContains(response, reverse("projects:create"))


class ProjectCreateTests(ProjectTestCase):
    def test_creates_project_with_normalized_url(self):
        response = self.client.post(
            reverse("projects:create"),
            {"name": "Mama Lishe", "website_url": "MamaLishe.example", "business_details": ""},
        )

        project = Project.objects.get(name="Mama Lishe")
        self.assertRedirects(response, project.get_absolute_url())
        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.website_url, "https://mamalishe.example/")

    def test_owner_cannot_be_set_from_the_form(self):
        self.client.post(
            reverse("projects:create"),
            {"name": "Sneaky", "business_details": "x", "owner": self.other.pk},
        )

        self.assertEqual(Project.objects.get(name="Sneaky").owner, self.owner)

    def test_creates_project_without_website_using_manual_details(self):
        self.client.post(
            reverse("projects:create"),
            {"name": "Fundi Seremala", "website_url": "", "business_details": "Furniture in Dodoma."},
        )

        project = Project.objects.get(name="Fundi Seremala")
        self.assertEqual(project.website_url, "")
        self.assertEqual(project.business_details, "Furniture in Dodoma.")
        self.resolver.assert_not_called()

    def test_requires_website_or_details(self):
        response = self.client.post(
            reverse("projects:create"), {"name": "Empty", "website_url": "", "business_details": "  "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a website address or describe your business.")
        self.assertFalse(Project.objects.filter(name="Empty").exists())

    def test_private_network_url_is_rejected_with_clear_message(self):
        self.resolver.side_effect = lambda hostname, port: ["10.0.0.5"]

        response = self.client.post(
            reverse("projects:create"),
            {"name": "Internal", "website_url": "https://intranet.example/"},
        )

        self.assertContains(response, "private or reserved network")
        self.assertFalse(Project.objects.filter(name="Internal").exists())

    def test_unsafe_urls_are_rejected(self):
        for url in ["http://127.0.0.1/", "http://169.254.169.254/", "file:///etc/passwd",
                    "https://localhost/", "javascript:alert(1)"]:
            with self.subTest(url=url):
                response = self.client.post(
                    reverse("projects:create"), {"name": "Bad", "website_url": url}
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(Project.objects.filter(name="Bad").exists())

    def test_unknown_domain_offers_manual_entry(self):
        self.resolver.side_effect = UnsafeURLError("dns_failed", "We could not find this website address. Check the spelling, or enter your business details manually.")

        response = self.client.post(
            reverse("projects:create"), {"name": "Typo", "website_url": "amiina.exmaple"}
        )

        self.assertContains(response, "enter your business details manually")

    def test_business_details_length_is_limited(self):
        response = self.client.post(
            reverse("projects:create"),
            {"name": "Long", "business_details": "x" * 5001},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(name="Long").exists())


class OwnershipTests(ProjectTestCase):
    """Changing the ID in the URL must never expose another user's project."""

    def test_other_users_project_is_not_found_on_every_page(self):
        pk = self.others_project.pk
        for name in ["projects:detail", "projects:update", "projects:delete"]:
            with self.subTest(view=name):
                response = self.client.get(reverse(name, args=[pk]))
                self.assertEqual(response.status_code, 404)
                self.assertNotContains(response, "Baraka Tours", status_code=404)

    def test_cannot_edit_other_users_project(self):
        response = self.client.post(
            reverse("projects:update", args=[self.others_project.pk]),
            {"name": "Hijacked", "business_details": "x"},
        )

        self.assertEqual(response.status_code, 404)
        self.others_project.refresh_from_db()
        self.assertEqual(self.others_project.name, "Baraka Tours")

    def test_cannot_delete_other_users_project(self):
        response = self.client.post(reverse("projects:delete", args=[self.others_project.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Project.objects.filter(pk=self.others_project.pk).exists())


class ProjectDetailUpdateDeleteTests(ProjectTestCase):
    def test_detail_shows_project_and_honest_status(self):
        response = self.client.get(self.project.get_absolute_url())

        self.assertContains(response, "Duka la Amina")
        self.assertContains(response, "Analyze website")
        self.assertContains(response, "Business profile review and content creation are not available yet.")

    def test_user_content_is_escaped(self):
        self.project.business_details = "<script>alert('x')</script>"
        self.project.save()

        response = self.client.get(self.project.get_absolute_url())

        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

    def test_update_saves_changes(self):
        response = self.client.post(
            reverse("projects:update", args=[self.project.pk]),
            {"name": "Duka Jipya", "business_name": "Amina Fashion",
             "website_url": "https://amina.example/", "business_details": ""},
        )

        self.assertRedirects(response, self.project.get_absolute_url())
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Duka Jipya")

    def test_delete_requires_confirmation_by_post(self):
        url = reverse("projects:delete", args=[self.project.pk])

        response = self.client.get(url)
        self.assertContains(response, "cannot be undone")
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse("projects:list"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_deleting_a_user_deletes_their_projects_only(self):
        self.other.delete()

        self.assertFalse(Project.objects.filter(name="Baraka Tours").exists())
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
