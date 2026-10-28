import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from apps.business_profiles.models import FactKey, ProfileFact
from apps.marketing_content.generation import confirmed_facts
from apps.marketing_content.models import ContentDraft
from apps.marketing_content.validation import find_unsupported_claims
from apps.projects.models import Project

from .forms import ImportForm, PosterForm, UploadForm
from .importing import ImportAlreadyRunning, candidate_images, request_import
from .models import Asset, Poster
from .posters import render_poster


def _owned_project(request, project_pk):
    return get_object_or_404(Project, pk=project_pk, owner=request.user)


def _read(field):
    with field.open("rb") as handle:
        return handle.read()


def _stream(field, filename, download=False):
    """Stream a private file after the caller has checked ownership."""
    try:
        handle = field.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("File missing")
    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type, as_attachment=download, filename=filename)
    response["Cache-Control"] = "private, max-age=300"
    return response


@login_required
@require_safe
def library(request, project_pk):
    project = _owned_project(request, project_pk)
    latest_import = project.image_imports.first()
    return render(request, "creative_assets/library.html", {
        "project": project,
        "assets": project.assets.all(),
        "posters": project.posters.all(),
        "latest_import": latest_import,
        "upload_form": UploadForm(),
        "has_candidates": bool(candidate_images(project)),
    })


@login_required
@require_POST
def upload(request, project_pk):
    project = _owned_project(request, project_pk)
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            with transaction.atomic():
                Asset.create_from_processed(
                    project=project, processed=form.processed, origin=Asset.Origin.UPLOAD,
                    kind=form.cleaned_data["kind"], alt_text=form.cleaned_data["alt_text"],
                    original_name=form.cleaned_data["image"].name[:200], rights_confirmed=True,
                )
            messages.success(request, _("Image added to your library."))
        except IntegrityError:
            messages.info(request, _("This image is already in your library."))
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("creative_assets:library", project_pk=project.pk)


@login_required
@require_http_methods(["GET", "POST"])
def import_from_website(request, project_pk):
    project = _owned_project(request, project_pk)
    candidates = candidate_images(project)
    form = ImportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            request_import(project, request.POST.getlist("urls"))
        except ValueError:
            messages.error(request, _("Choose at least one image."))
        except ImportAlreadyRunning:
            messages.info(request, _("An import is already in progress."))
        else:
            messages.success(request, _("Importing the selected images."))
            return redirect("creative_assets:library", project_pk=project.pk)
    return render(request, "creative_assets/import.html", {
        "project": project, "candidates": candidates, "form": form,
    })


@login_required
@require_safe
def asset_file(request, project_pk, pk, variant):
    asset = get_object_or_404(Asset, pk=pk, project_id=project_pk, project__owner=request.user)
    field = asset.thumbnail if variant == "thumb" else asset.file
    return _stream(field, f"image-{asset.pk}.{field.name.rsplit('.', 1)[-1]}")


@login_required
@require_POST
def asset_delete(request, project_pk, pk):
    asset = get_object_or_404(Asset, pk=pk, project_id=project_pk, project__owner=request.user)
    asset.delete()
    messages.success(request, _("Image removed. Posters made with it are kept."))
    return redirect("creative_assets:library", project_pk=project_pk)


@login_required
@require_http_methods(["GET", "POST"])
def poster_create(request, project_pk):
    project = _owned_project(request, project_pk)
    initial = {"brand_color": "#0b6e4f"}
    brand = ProfileFact.objects.filter(profile__project=project, key=FactKey.BRAND_COLOR,
                                       status=ProfileFact.Status.CONFIRMED).first()
    if brand and len(brand.value) == 7:
        initial["brand_color"] = brand.value
    script = None
    script_id = request.GET.get("script") or request.POST.get("script")
    if script_id and str(script_id).isdigit():
        script = ContentDraft.objects.filter(
            pk=script_id, kind=ContentDraft.Kind.SCRIPT, status=ContentDraft.Status.APPROVED,
            brief__project=project,
        ).first()
        if script:
            initial.update(headline=script.data.get("headline") or script.title,
                           call_to_action=script.data.get("call_to_action", "")[:80])

    form = PosterForm(request.POST or None, initial=initial, project=project)
    if request.method == "POST" and form.is_valid():
        poster = form.save(commit=False)
        poster.project, poster.script = project, script
        poster.width, poster.height = Poster.SIZES[poster.format]
        photo = _read(poster.background.file) if poster.background else None
        logo = _read(poster.logo.file) if poster.logo else None
        content = render_poster(
            size=(poster.width, poster.height), headline=poster.headline, subtext=poster.subtext,
            call_to_action=poster.call_to_action, brand_color=poster.brand_color,
            photo_bytes=photo, logo_bytes=logo,
        )
        poster.flags = find_unsupported_claims(
            [(name, getattr(poster, name)) for name in ("headline", "subtext", "call_to_action")
             if getattr(poster, name)],
            confirmed_facts(project),
        )
        poster.file.save("poster.jpg", ContentFile(content), save=False)
        poster.save()
        messages.success(request, _("Poster created."))
        return redirect(poster)
    return render(request, "creative_assets/poster_form.html", {
        "project": project, "form": form, "script": script,
        "has_images": project.assets.filter(rights_confirmed=True).exists(),
    })


@login_required
@require_safe
def poster_detail(request, project_pk, pk):
    poster = get_object_or_404(Poster, pk=pk, project_id=project_pk, project__owner=request.user)
    return render(request, "creative_assets/poster_detail.html", {"project": poster.project, "poster": poster})


@login_required
@require_safe
def poster_file(request, project_pk, pk):
    poster = get_object_or_404(Poster, pk=pk, project_id=project_pk, project__owner=request.user)
    return _stream(poster.file, f"poster-{poster.pk}-{poster.format}.jpg",
                   download=request.GET.get("download") == "1")


@login_required
@require_POST
def poster_delete(request, project_pk, pk):
    poster = get_object_or_404(Poster, pk=pk, project_id=project_pk, project__owner=request.user)
    poster.delete()
    messages.success(request, _("Poster deleted."))
    return redirect("creative_assets:library", project_pk=project_pk)
