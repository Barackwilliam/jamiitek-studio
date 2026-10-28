from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_safe

from .forms import ProjectForm
from .models import Project


def _get_owned_project(request, pk):
    # Another user's project is reported as missing, not forbidden, so
    # project IDs reveal nothing about other accounts.
    return get_object_or_404(Project, pk=pk, owner=request.user)


@login_required
@require_safe
def project_list(request):
    projects = request.user.projects.all()
    return render(request, "projects/project_list.html", {"projects": projects})


@login_required
@require_http_methods(["GET", "POST"])
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, _("Project created."))
        return redirect(project)
    return render(request, "projects/project_form.html", {"form": form, "is_new": True})


@login_required
@require_safe
def project_detail(request, pk):
    project = _get_owned_project(request, pk)
    return render(request, "projects/project_detail.html", {"project": project})


@login_required
@require_http_methods(["GET", "POST"])
def project_update(request, pk):
    project = _get_owned_project(request, pk)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Project saved."))
        return redirect(project)
    return render(
        request, "projects/project_form.html", {"form": form, "project": project, "is_new": False}
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_delete(request, pk):
    project = _get_owned_project(request, pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, _("Project deleted."))
        return redirect("projects:list")
    return render(request, "projects/project_confirm_delete.html", {"project": project})
