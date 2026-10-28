from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.business_profiles.models import BusinessProfile, FactKey, ProfileFact
from apps.marketing_content.models import ContentDraft, MarketingBrief
from apps.media_production.models import VideoRender
from apps.projects.models import Project
from apps.projects.progress import project_steps
from apps.website_analyzer.models import WebsiteAnalysis


def states(project):
    return [("done" if s.done else "next" if s.is_next else "skipped" if s.skipped else "later")
            for s in project_steps(project)]


class ProjectProgressTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("amina", password="test-pass-123!")

    def make_project(self, **fields):
        fields.setdefault("website_url", "https://amina.example/")
        return Project.objects.create(owner=self.owner, name="Duka", **fields)

    def test_new_project_with_website_starts_with_analysis(self):
        project = self.make_project()
        self.assertEqual(states(project), ["next", "later", "later", "later"])

    def test_without_website_analysis_is_not_needed(self):
        project = self.make_project(website_url="", business_details="Tunauza vitenge.")
        self.assertEqual(states(project), ["skipped", "next", "later", "later"])

    def test_failed_or_running_analysis_does_not_count(self):
        project = self.make_project()
        WebsiteAnalysis.objects.create(project=project, start_url=project.website_url, status="failed")
        running = WebsiteAnalysis.objects.create(project=project, start_url=project.website_url,
                                                 status="running")
        self.assertEqual(states(project)[0], "next")
        running.status = "partial"
        running.save()
        self.assertEqual(states(project)[0], "done")

    def test_steps_follow_saved_work(self):
        project = self.make_project()
        WebsiteAnalysis.objects.create(project=project, start_url=project.website_url, status="completed")
        profile = BusinessProfile.objects.create(project=project)
        fact = ProfileFact.objects.create(profile=profile, key=FactKey.PHONE, value="0754 123 456",
                                          source="website", status="suggested")
        self.assertEqual(states(project), ["done", "next", "later", "later"])

        fact.status = "confirmed"
        fact.save()
        brief = MarketingBrief.objects.create(project=project, objective="sales", audience="x",
                                              platform="instagram")
        script = ContentDraft.objects.create(brief=brief, kind="script", status="edited", data={"title": "x"})
        ContentDraft.objects.create(brief=brief, kind="concept", status="approved", data={"title": "x"})
        self.assertEqual(states(project), ["done", "done", "next", "later"])

        script.status = "approved"
        script.save()
        VideoRender.objects.create(project=project, script=script, status="failed")
        self.assertEqual(states(project), ["done", "done", "done", "next"])

        VideoRender.objects.create(project=project, script=script, status="completed")
        self.assertEqual(states(project), ["done", "done", "done", "done"])

    def test_other_projects_do_not_count(self):
        project = self.make_project()
        other = self.make_project()
        WebsiteAnalysis.objects.create(project=other, start_url=other.website_url, status="completed")
        self.assertEqual(states(project)[0], "next")

    def test_project_page_shows_checklist_with_next_step_link(self):
        project = self.make_project()
        self.client.force_login(self.owner)
        response = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertContains(response, "Getting started")
        self.assertContains(response, 'aria-current="step"', count=1)
        self.assertContains(response, f'href="/projects/{project.pk}/#analysis-heading"')
