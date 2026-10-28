"""Importing images the user selected from their analyzed website.

Only images found by the project's latest website analysis can be imported,
each is fetched with the SSRF-safe fetcher (honouring robots.txt and a
polite delay), and each passes the same validation and re-encoding as an
upload. The user confirms their right to use the images when importing.
"""

import logging
import time

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_noop

from apps.business_profiles.models import FactKey, ProfileFact
from apps.website_analyzer.crawler import RobotsCache
from apps.website_analyzer.fetch import FetchError, safe_fetch
from apps.website_analyzer.models import AnalyzedPage, WebsiteAnalysis
from apps.website_analyzer.url_safety import UnsafeURLError

from .images import InvalidImage, process_image
from .models import Asset, ImageImportJob

logger = logging.getLogger(__name__)

IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
MAX_CANDIDATES = 60
MAX_PER_IMPORT = 12


class ImportAlreadyRunning(Exception):
    pass


def candidate_images(project):
    """Images found on the website by the latest finished analysis, logos first."""
    analysis = project.analyses.filter(
        status__in=[WebsiteAnalysis.Status.COMPLETED, WebsiteAnalysis.Status.PARTIAL]
    ).first()
    candidates = {}

    logo_urls = ProfileFact.objects.filter(
        profile__project=project, key=FactKey.LOGO
    ).exclude(status=ProfileFact.Status.REJECTED).values_list("value", flat=True)
    for url in logo_urls:
        if url.startswith(("http://", "https://")):
            candidates.setdefault(url, {"url": url, "alt": "", "page": "", "is_logo": True})

    if analysis:
        pages = analysis.pages.filter(status=AnalyzedPage.Status.SUCCESS).order_by("position")
        for page in pages:
            for image in page.images:
                url = image.get("url", "")
                if url:
                    candidates.setdefault(url, {"url": url, "alt": image.get("alt", ""),
                                                "page": page.url, "is_logo": False})
    return list(candidates.values())[:MAX_CANDIDATES]


def request_import(project, urls):
    allowed = {c["url"] for c in candidate_images(project)}
    selected = [url for url in dict.fromkeys(urls) if url in allowed][:MAX_PER_IMPORT]
    if not selected:
        raise ValueError("no valid images selected")
    if project.image_imports.filter(status__in=ImageImportJob.ACTIVE_STATUSES).exists():
        raise ImportAlreadyRunning()
    try:
        with transaction.atomic():
            return ImageImportJob.objects.create(project=project, urls=selected)
    except IntegrityError:
        raise ImportAlreadyRunning()


def claim_next_import():
    for pk in ImageImportJob.objects.filter(status=ImageImportJob.Status.QUEUED).order_by(
            "created_at", "id").values_list("pk", flat=True)[:5]:
        if ImageImportJob.objects.filter(pk=pk, status=ImageImportJob.Status.QUEUED).update(
                status=ImageImportJob.Status.RUNNING, started_at=timezone.now()):
            return ImageImportJob.objects.select_related("project").get(pk=pk)
    return None


def fail_stale_imports():
    cutoff = timezone.now() - timezone.timedelta(minutes=15)
    return ImageImportJob.objects.filter(
        status=ImageImportJob.Status.RUNNING, started_at__lt=cutoff
    ).update(status=ImageImportJob.Status.FAILED, finished_at=timezone.now())


def run_import(job, fetch=safe_fetch, sleep=time.sleep, delay=1.0):
    project = job.project
    candidates = {c["url"]: c for c in candidate_images(project)}
    robots = RobotsCache(fetch)
    results = []
    for index, url in enumerate(job.urls):
        if index:
            sleep(delay)
        candidate = candidates.get(url, {"alt": "", "is_logo": False})
        try:
            if robots.problem(url) or not robots.allowed(url):
                raise FetchError("robots", "The website does not allow this image to be downloaded.")
            response = fetch(url, allowed_content_types=IMAGE_CONTENT_TYPES,
                             max_bytes=settings.MAX_IMAGE_BYTES, total_timeout=30.0)
            if not 200 <= response.status < 300:
                raise FetchError("http_status", f"The website answered with status {response.status}.")
            processed = process_image(response.body, settings.MAX_IMAGE_BYTES)
            try:
                with transaction.atomic():
                    Asset.create_from_processed(
                        project=project, processed=processed, origin=Asset.Origin.WEBSITE,
                        kind=Asset.Kind.LOGO if candidate["is_logo"] else Asset.Kind.IMAGE,
                        source_url=url, alt_text=candidate["alt"][:300], rights_confirmed=True,
                    )
            except IntegrityError:
                results.append({"url": url, "status": "duplicate", "message": gettext_noop("Already in your library.")})
                continue
            results.append({"url": url, "status": "imported", "message": ""})
        except (FetchError, UnsafeURLError, InvalidImage) as exc:
            results.append({"url": url, "status": "failed", "message": exc.message})
        except Exception:
            logger.exception("Image import failed for %s", url)
            results.append({"url": url, "status": "failed", "message": gettext_noop("Something went wrong on our side.")})
    job.results = results
    job.status = (ImageImportJob.Status.COMPLETED
                  if any(r["status"] != "failed" for r in results) else ImageImportJob.Status.FAILED)
    job.finished_at = timezone.now()
    job.save()
    return job
