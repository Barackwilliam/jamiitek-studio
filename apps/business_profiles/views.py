from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from apps.projects.models import Project
from apps.website_analyzer.models import WebsiteAnalysis

from .forms import AddFactForm, FactValueForm
from .models import ESSENTIAL_KEYS, SINGLE_VALUE_KEYS, BusinessProfile, FactKey, ProfileFact
from .suggestions import refresh_suggestions


def _owned_project(request, project_pk):
    return get_object_or_404(Project, pk=project_pk, owner=request.user)


def _owned_fact(request, project_pk, pk):
    return get_object_or_404(
        ProfileFact.objects.select_related("profile__project"),
        pk=pk,
        profile__project_id=project_pk,
        profile__project__owner=request.user,
    )


def _profile_sections(profile):
    facts = list(profile.facts.all()) if profile else []
    sections = []
    for key in FactKey:
        key_facts = [fact for fact in facts if fact.key == key]
        active = [fact for fact in key_facts if fact.status != ProfileFact.Status.REJECTED]
        if not key_facts and key not in ESSENTIAL_KEYS:
            continue
        sections.append({
            "key": key,
            "label": key.label,
            "facts": key_facts,
            "conflict": key in SINGLE_VALUE_KEYS and len(active) > 1,
            "missing": key in ESSENTIAL_KEYS and not active,
        })
    return sections


@login_required
@require_safe
def profile_detail(request, project_pk):
    project = _owned_project(request, project_pk)
    profile = BusinessProfile.objects.filter(project=project).first()
    sections = _profile_sections(profile)
    facts = [fact for section in sections for fact in section["facts"]]
    latest_analysis = project.analyses.filter(
        status__in=[WebsiteAnalysis.Status.COMPLETED, WebsiteAnalysis.Status.PARTIAL]
    ).first()
    return render(request, "business_profiles/profile_detail.html", {
        "project": project,
        "profile": profile,
        "sections": sections,
        "to_review": sum(1 for f in facts if f.status == ProfileFact.Status.SUGGESTED),
        "confirmed": sum(1 for f in facts if f.status == ProfileFact.Status.CONFIRMED),
        "missing": [s["label"] for s in sections if s["missing"]],
        "latest_analysis": latest_analysis,
        "add_form": AddFactForm(),
    })


@login_required
@require_POST
def refresh_from_analysis(request, project_pk):
    project = _owned_project(request, project_pk)
    analysis = project.analyses.filter(
        status__in=[WebsiteAnalysis.Status.COMPLETED, WebsiteAnalysis.Status.PARTIAL]
    ).first()
    if analysis is None:
        messages.error(request, _("There is no finished website analysis to take suggestions from."))
    else:
        _profile, created = refresh_suggestions(project, analysis)
        messages.success(
            request, _("Suggestions updated from the latest analysis: %(count)d to review.")
            % {"count": created},
        )
    return redirect("business_profiles:detail", project_pk=project.pk)


@login_required
@require_POST
def add_fact(request, project_pk):
    project = _owned_project(request, project_pk)
    profile, _created = BusinessProfile.objects.get_or_create(project=project)
    form = AddFactForm(request.POST, profile=profile)
    if form.is_valid():
        ProfileFact.objects.create(
            profile=profile,
            key=form.cleaned_data["key"],
            value=form.cleaned_data["value"],
            source=ProfileFact.Source.USER,
            status=ProfileFact.Status.CONFIRMED,
        )
        messages.success(request, _("Information added."))
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("business_profiles:detail", project_pk=project.pk)


@login_required
@require_POST
def set_fact_status(request, project_pk, pk):
    fact = _owned_fact(request, project_pk, pk)
    action = request.POST.get("action")
    if action == "confirm":
        fact.status = ProfileFact.Status.CONFIRMED
    elif action == "reject" and fact.source == ProfileFact.Source.WEBSITE:
        fact.status = ProfileFact.Status.REJECTED
    elif action == "undo" and fact.source == ProfileFact.Source.WEBSITE:
        fact.status = ProfileFact.Status.SUGGESTED
    elif action == "delete" and fact.source == ProfileFact.Source.USER:
        fact.delete()
        messages.success(request, _("Information removed."))
        return redirect("business_profiles:detail", project_pk=project_pk)
    else:
        messages.error(request, _("That action is not available for this information."))
        return redirect("business_profiles:detail", project_pk=project_pk)
    fact.save(update_fields=["status", "updated_at"])
    return redirect(f"{fact.profile.get_absolute_url()}#fact-{fact.pk}")


@login_required
@require_http_methods(["GET", "POST"])
def edit_fact(request, project_pk, pk):
    fact = _owned_fact(request, project_pk, pk)
    form = FactValueForm(
        request.POST or None,
        initial={"value": fact.value},
        profile=fact.profile,
        key=fact.key,
        instance=fact,
    )
    if request.method == "POST" and form.is_valid():
        new_value = form.cleaned_data["value"]
        if new_value != fact.value:
            if fact.source == ProfileFact.Source.WEBSITE and not fact.original_value:
                fact.original_value = fact.value
            fact.value = new_value
            fact.edited_by_user = True
        # Saving an edit is an explicit decision about this value.
        fact.status = ProfileFact.Status.CONFIRMED
        fact.save()
        messages.success(request, _("Saved and confirmed."))
        return redirect(f"{fact.profile.get_absolute_url()}#fact-{fact.pk}")
    return render(request, "business_profiles/fact_edit.html", {
        "fact": fact, "project": fact.profile.project, "form": form,
    })
