from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from apps.projects.models import Project
from integrations.ai.registry import text_provider_is_configured

from .forms import ApproveForm, BriefForm, SceneFormSet, ScriptForm
from .generation import GenerationAlreadyRunning, confirmed_facts, request_concepts, request_script
from .models import ContentDraft, DraftRevision, MarketingBrief
from .validation import find_unsupported_claims, script_texts


def _owned_project(request, project_pk):
    return get_object_or_404(Project, pk=project_pk, owner=request.user)


def _owned_brief(request, project_pk, pk):
    return get_object_or_404(MarketingBrief.objects.select_related("project"),
                             pk=pk, project_id=project_pk, project__owner=request.user)


def _owned_draft(request, project_pk, pk, kind):
    return get_object_or_404(ContentDraft.objects.select_related("brief__project"),
                             pk=pk, kind=kind, brief__project_id=project_pk,
                             brief__project__owner=request.user)


def _ai_context():
    return {
        "ai_ready": text_provider_is_configured(),
        "ai_provider_name": settings.AI_TEXT_PROVIDER_NAME,
        "ai_data_notice": settings.AI_TEXT_DATA_NOTICE,
    }


def _queue_feedback(request, queue, *args):
    try:
        queue(*args)
    except GenerationAlreadyRunning:
        messages.info(request, _("The AI is already writing for this brief. Please wait for it to finish."))
        return False
    return True


@login_required
@require_safe
def content_home(request, project_pk):
    project = _owned_project(request, project_pk)
    return render(request, "marketing_content/content_home.html", {
        "project": project,
        "briefs": project.briefs.all(),
        "fact_count": len(confirmed_facts(project)),
        **_ai_context(),
    })


@login_required
@require_http_methods(["GET", "POST"])
def brief_create(request, project_pk):
    project = _owned_project(request, project_pk)
    fact_count = len(confirmed_facts(project))
    form = BriefForm(request.POST or None)
    if request.method == "POST":
        if not text_provider_is_configured():
            messages.error(request, _("AI text generation is not set up on this installation yet."))
        elif fact_count == 0:
            messages.error(request, _("Confirm or add business information in the profile first."))
        elif form.is_valid():
            brief = form.save(commit=False)
            brief.project = project
            brief.save()
            request_concepts(brief)
            messages.success(request, _("The AI is writing three concepts."))
            return redirect(brief)
    return render(request, "marketing_content/brief_form.html", {
        "project": project, "form": form, "fact_count": fact_count, **_ai_context(),
    })


@login_required
@require_safe
def brief_detail(request, project_pk, pk):
    brief = _owned_brief(request, project_pk, pk)
    drafts = list(brief.drafts.all())
    return render(request, "marketing_content/brief_detail.html", {
        "project": brief.project,
        "brief": brief,
        "latest_job": brief.jobs.first(),
        "concepts": [d for d in drafts if d.kind == ContentDraft.Kind.CONCEPT],
        "scripts": [d for d in drafts if d.kind == ContentDraft.Kind.SCRIPT],
        **_ai_context(),
    })


@login_required
@require_POST
def regenerate_concepts(request, project_pk, pk):
    brief = _owned_brief(request, project_pk, pk)
    if _queue_feedback(request, request_concepts, brief):
        messages.success(request, _("The AI is writing new concepts. Earlier ones are kept."))
    return redirect(brief)


@login_required
@require_POST
def write_script(request, project_pk, pk):
    concept = _owned_draft(request, project_pk, pk, ContentDraft.Kind.CONCEPT)
    if _queue_feedback(request, request_script, concept.brief, concept):
        messages.success(request, _("The AI is writing the script."))
    return redirect(concept.brief)


def _script_context(script, **extra):
    lookup = script.fact_lookup()
    scenes = [
        {**scene, "facts": [lookup[ref] for ref in scene.get("fact_ids", []) if ref in lookup]}
        for scene in script.data.get("scenes", [])
    ]
    return {
        "project": script.brief.project,
        "brief": script.brief,
        "script": script,
        "scenes": scenes,
        "total_seconds": sum(scene.get("duration_seconds", 0) for scene in scenes),
        "facts_used": [lookup[ref] for ref in script.data.get("fact_ids", []) if ref in lookup],
        **extra,
    }


@login_required
@require_safe
def script_detail(request, project_pk, pk):
    script = _owned_draft(request, project_pk, pk, ContentDraft.Kind.SCRIPT)
    return render(request, "marketing_content/script_detail.html", _script_context(
        script, approve_form=ApproveForm(needs_check=bool(script.flags)),
        revisions=script.revisions.all()[:DraftRevision.MAX_PER_DRAFT]))


@login_required
@require_POST
def script_restore(request, project_pk, pk, revision_pk):
    script = _owned_draft(request, project_pk, pk, ContentDraft.Kind.SCRIPT)
    revision = get_object_or_404(DraftRevision, pk=revision_pk, draft=script)
    DraftRevision.save_from(script)
    script.data = revision.data
    script.flags = find_unsupported_claims(script_texts(script.data), script.facts)
    # A restored version must be reviewed and approved again.
    script.status = ContentDraft.Status.EDITED
    script.approved_at = None
    script.save()
    messages.success(request, _("Earlier version restored. Review it before approving."))
    return redirect(script)


@login_required
@require_http_methods(["GET", "POST"])
def script_edit(request, project_pk, pk):
    script = _owned_draft(request, project_pk, pk, ContentDraft.Kind.SCRIPT)
    data = script.data
    form = ScriptForm(request.POST or None, initial={**data, "hashtags": " ".join(data.get("hashtags", []))})
    formset = SceneFormSet(request.POST or None, initial=data.get("scenes", []), prefix="scenes")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        scenes = []
        old_scenes = data.get("scenes", [])
        for index, scene_form in enumerate(formset.forms):
            if scene_form.cleaned_data.get("DELETE"):
                continue
            scene = {k: v for k, v in scene_form.cleaned_data.items() if k != "DELETE"}
            # Keep the fact references of scenes that already existed.
            scene["fact_ids"] = old_scenes[index].get("fact_ids", []) if index < len(old_scenes) else []
            scenes.append(scene)
        DraftRevision.save_from(script)
        script.data = {**data, **form.cleaned_data, "scenes": scenes}
        script.flags = find_unsupported_claims(script_texts(script.data), script.facts)
        script.status = ContentDraft.Status.EDITED
        script.approved_at = None
        script.save()
        messages.success(request, _("Script saved. Review it again before approving."))
        return redirect(script)
    return render(request, "marketing_content/script_edit.html", {
        "project": script.brief.project, "script": script, "form": form, "formset": formset,
    })


@login_required
@require_POST
def script_approve(request, project_pk, pk):
    script = _owned_draft(request, project_pk, pk, ContentDraft.Kind.SCRIPT)
    form = ApproveForm(request.POST, needs_check=bool(script.flags))
    if not form.is_valid():
        return render(request, "marketing_content/script_detail.html",
                      _script_context(script, approve_form=form), status=400)
    script.status = ContentDraft.Status.APPROVED
    script.approved_at = timezone.now()
    script.save(update_fields=["status", "approved_at", "updated_at"])
    messages.success(request, _("Script approved."))
    return redirect(script)
