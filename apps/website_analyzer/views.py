from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_safe

from apps.projects.models import Project

from .jobs import AnalysisAlreadyRunning, request_analysis
from .models import WebsiteAnalysis


@login_required
@require_POST
def start_analysis(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    if not project.website_url:
        messages.error(request, _("Add a website address to this project before analyzing it."))
        return redirect(project)
    try:
        analysis = request_analysis(project)
    except AnalysisAlreadyRunning as exc:
        messages.info(request, _("An analysis of this website is already in progress."))
        return redirect(exc.analysis or project)
    messages.success(request, _("Website analysis started."))
    return redirect(analysis)


@login_required
@require_safe
def analysis_detail(request, project_pk, pk):
    analysis = get_object_or_404(
        WebsiteAnalysis.objects.select_related("project"),
        pk=pk,
        project_id=project_pk,
        project__owner=request.user,
    )
    pages = analysis.pages.all()
    return render(
        request,
        "website_analyzer/analysis_detail.html",
        {"analysis": analysis, "project": analysis.project, "pages": pages},
    )
