from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.business_profiles.models import BusinessProfile, FactKey, ProfileFact
from apps.projects.models import Project
from apps.website_analyzer.models import AnalyzedPage, WebsiteAnalysis

SITE = "https://duka.example/"


class ProfileViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("asha", password="x-pass-123!")
        cls.other = User.objects.create_user("bakari", password="x-pass-123!")
        cls.project = Project.objects.create(owner=cls.owner, name="Duka", website_url=SITE,
                                             business_details="Tunauza vitenge.")
        cls.profile = BusinessProfile.objects.create(project=cls.project)
        cls.suggested = ProfileFact.objects.create(
            profile=cls.profile, key=FactKey.PHONE, value="0754 123 456", source="website",
            evidence=[{"url": SITE + "contact", "detail": "Page text"}],
        )
        cls.user_fact = ProfileFact.objects.create(
            profile=cls.profile, key=FactKey.OFFERING, value="Vitenge", source="user", status="confirmed",
        )
        other_project = Project.objects.create(owner=cls.other, name="Siri", business_details="x")
        cls.other_fact = ProfileFact.objects.create(
            profile=BusinessProfile.objects.create(project=other_project),
            key=FactKey.PHONE, value="0700 000 000", source="website",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def url(self, name, *args):
        return reverse(f"business_profiles:{name}", args=[self.project.pk, *args])

    def post_status(self, fact, action, project=None):
        project_pk = (project or self.project).pk
        return self.client.post(
            reverse("business_profiles:set_status", args=[project_pk, fact.pk]), {"action": action}
        )


class ProfileDetailTests(ProfileViewTestCase):
    def test_shows_facts_status_evidence_and_missing_information(self):
        response = self.client.get(self.url("detail"))

        self.assertContains(response, "0754 123 456")
        self.assertContains(response, "Needs your review")
        self.assertContains(response, SITE + "contact")
        self.assertContains(response, "Tunauza vitenge.")
        self.assertContains(response, "Missing:")
        self.assertContains(response, "Business name")
        self.assertContains(response, "1 item needs your review")

    def test_profile_page_without_profile_does_not_create_one(self):
        project = Project.objects.create(owner=self.owner, name="Mpya", business_details="x")

        response = self.client.get(reverse("business_profiles:detail", args=[project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(BusinessProfile.objects.filter(project=project).exists())

    def test_conflicting_single_values_are_flagged(self):
        for name in ["Duka la Asha", "Asha Fashion"]:
            ProfileFact.objects.create(profile=self.profile, key=FactKey.BUSINESS_NAME, value=name,
                                       source="website")

        response = self.client.get(self.url("detail"))

        self.assertContains(response, "Different values were found")

    def test_website_values_are_escaped(self):
        ProfileFact.objects.create(profile=self.profile, key=FactKey.DESCRIPTION,
                                   value="<img src=x onerror=alert(1)>", source="website")

        response = self.client.get(self.url("detail"))

        self.assertNotContains(response, "<img src=x")
        self.assertContains(response, "&lt;img src=x onerror=alert(1)&gt;")


class FactActionTests(ProfileViewTestCase):
    def test_confirm_reject_and_undo(self):
        self.post_status(self.suggested, "confirm")
        self.suggested.refresh_from_db()
        self.assertEqual(self.suggested.status, "confirmed")

        self.post_status(self.suggested, "undo")
        self.post_status(self.suggested, "reject")
        self.suggested.refresh_from_db()
        self.assertEqual(self.suggested.status, "rejected")

    def test_user_facts_can_be_removed_but_not_rejected(self):
        self.post_status(self.user_fact, "reject")
        self.user_fact.refresh_from_db()
        self.assertEqual(self.user_fact.status, "confirmed")

        self.post_status(self.user_fact, "delete")
        self.assertFalse(ProfileFact.objects.filter(pk=self.user_fact.pk).exists())

    def test_website_facts_cannot_be_deleted(self):
        self.post_status(self.suggested, "delete")
        self.assertTrue(ProfileFact.objects.filter(pk=self.suggested.pk).exists())

    def test_actions_require_post(self):
        response = self.client.get(self.url("set_status", self.suggested.pk))
        self.assertEqual(response.status_code, 405)

    def test_edit_confirms_and_keeps_original_wording(self):
        response = self.client.post(self.url("edit_fact", self.suggested.pk), {"value": "+255 754 123 456"})

        self.assertEqual(response.status_code, 302)
        self.suggested.refresh_from_db()
        self.assertEqual(self.suggested.value, "+255 754 123 456")
        self.assertEqual(self.suggested.original_value, "0754 123 456")
        self.assertTrue(self.suggested.edited_by_user)
        self.assertEqual(self.suggested.status, "confirmed")

    def test_edit_rejects_duplicate_and_empty_values(self):
        for value in ["   ", "vitenge"]:
            with self.subTest(value=value):
                response = self.client.post(self.url("edit_fact", self.user_fact.pk), {"value": value})
                if value.strip():
                    self.assertEqual(response.status_code, 302)  # same fact, same value is fine
                else:
                    self.assertContains(response, "This field is required")

        ProfileFact.objects.create(profile=self.profile, key=FactKey.OFFERING, value="Ushonaji",
                                   source="user", status="confirmed")
        response = self.client.post(self.url("edit_fact", self.user_fact.pk), {"value": "USHONAJI"})
        self.assertContains(response, "already in the profile")

    def test_add_fact_is_confirmed_user_information(self):
        self.client.post(self.url("add_fact"), {"key": FactKey.ADDRESS, "value": "Sokoni, Arusha"})

        fact = self.profile.facts.get(key=FactKey.ADDRESS)
        self.assertEqual((fact.source, fact.status), ("user", "confirmed"))

    def test_add_fact_validation(self):
        self.client.post(self.url("add_fact"), {"key": "not-a-key", "value": "x"})
        self.client.post(self.url("add_fact"), {"key": FactKey.PHONE, "value": "0754  123 456"})
        self.client.post(self.url("add_fact"), {"key": FactKey.BUSINESS_NAME, "value": "x" * 301})

        self.assertEqual(self.profile.facts.count(), 2)

    def test_add_fact_creates_profile_when_missing(self):
        project = Project.objects.create(owner=self.owner, name="Mpya", business_details="x")

        self.client.post(reverse("business_profiles:add_fact", args=[project.pk]),
                         {"key": FactKey.BUSINESS_NAME, "value": "Mpya Ltd"})

        self.assertEqual(project.business_profile.facts.get().value, "Mpya Ltd")


class ProfileOwnershipTests(ProfileViewTestCase):
    def test_other_users_profile_and_facts_are_not_found(self):
        other_project = self.other_fact.profile.project
        urls = [
            ("get", reverse("business_profiles:detail", args=[other_project.pk])),
            ("post", reverse("business_profiles:refresh", args=[other_project.pk])),
            ("post", reverse("business_profiles:add_fact", args=[other_project.pk])),
            ("get", reverse("business_profiles:edit_fact", args=[other_project.pk, self.other_fact.pk])),
            # Own project id with someone else's fact id:
            ("get", self.url("edit_fact", self.other_fact.pk)),
            ("post", self.url("set_status", self.other_fact.pk)),
        ]
        for method, url in urls:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url, {"action": "confirm", "key": "phone", "value": "1"})
                self.assertEqual(response.status_code, 404)
        self.other_fact.refresh_from_db()
        self.assertEqual(self.other_fact.status, "suggested")

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url("detail"))
        self.assertEqual(response.status_code, 302)


class RefreshViewTests(ProfileViewTestCase):
    def test_refresh_without_finished_analysis_explains(self):
        response = self.client.post(self.url("refresh"), follow=True)
        self.assertContains(response, "no finished website analysis")

    def test_refresh_uses_latest_finished_analysis(self):
        analysis = WebsiteAnalysis.objects.create(project=self.project, start_url=SITE,
                                                  status=WebsiteAnalysis.Status.PARTIAL)
        AnalyzedPage.objects.create(analysis=analysis, position=1, url=SITE, status="success",
                                    text="info@duka.example")

        response = self.client.post(self.url("refresh"), follow=True)

        self.assertContains(response, "1 to review")
        self.assertTrue(self.profile.facts.filter(key=FactKey.EMAIL).exists())
        # The user's own information is untouched; the old suggestion was replaced.
        self.assertTrue(ProfileFact.objects.filter(pk=self.user_fact.pk).exists())
        self.assertFalse(ProfileFact.objects.filter(pk=self.suggested.pk).exists())
