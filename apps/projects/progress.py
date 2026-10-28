"""The getting-started checklist shown on a project page.

Each step is worked out from what is saved, so the list is always current
and needs no extra columns. The first unfinished step is "next".
"""

from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@dataclass
class Step:
    label: str
    done: bool
    url: str
    hint: str = ""
    skipped: bool = False
    is_next: bool = False


def project_steps(project):
    # Imported here to keep the projects app free of import cycles.
    from apps.business_profiles.models import ProfileFact
    from apps.marketing_content.models import ContentDraft
    from apps.media_production.models import VideoRender
    from apps.website_analyzer.models import WebsiteAnalysis

    finished = (WebsiteAnalysis.Status.COMPLETED, WebsiteAnalysis.Status.PARTIAL)
    has_website = bool(project.website_url)
    steps = [
        Step(
            label=_("Analyze your website"),
            done=has_website and project.analyses.filter(status__in=finished).exists(),
            skipped=not has_website,
            url=reverse("projects:detail", args=[project.pk]) + "#analysis-heading",
            hint=_("No website: we use the details you entered."),
        ),
        Step(
            label=_("Confirm your business information"),
            done=ProfileFact.objects.filter(
                profile__project=project, status=ProfileFact.Status.CONFIRMED).exists(),
            url=reverse("business_profiles:detail", args=[project.pk]),
        ),
        Step(
            label=_("Approve a script"),
            done=ContentDraft.objects.filter(
                brief__project=project, kind=ContentDraft.Kind.SCRIPT,
                status=ContentDraft.Status.APPROVED).exists(),
            url=reverse("marketing_content:home", args=[project.pk]),
        ),
        Step(
            label=_("Make a poster or a video"),
            done=project.posters.exists()
            or project.videos.filter(status=VideoRender.Status.COMPLETED).exists(),
            url=reverse("creative_assets:library", args=[project.pk]),
        ),
    ]
    for step in steps:
        if not step.done and not step.skipped:
            step.is_next = True
            break
    return steps
