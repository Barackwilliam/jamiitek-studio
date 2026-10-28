"""Running website analyses outside the web request.

Jobs are rows in WebsiteAnalysis. The worker (`manage.py run_analysis_worker`)
claims a queued row with a conditional update, so two workers can never
process the same analysis, then saves each page as soon as it is crawled.
"""

import logging
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from .crawler import crawl
from .models import AnalyzedPage, WebsiteAnalysis
from .signals import analysis_finished

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=15)


class AnalysisAlreadyRunning(Exception):
    def __init__(self, analysis):
        super().__init__("An analysis is already queued or running for this project.")
        self.analysis = analysis


def request_analysis(project):
    """Queue an analysis for the project's website, or raise AnalysisAlreadyRunning."""
    active = project.analyses.filter(status__in=WebsiteAnalysis.ACTIVE_STATUSES).first()
    if active:
        raise AnalysisAlreadyRunning(active)
    try:
        with transaction.atomic():
            return WebsiteAnalysis.objects.create(project=project, start_url=project.website_url)
    except IntegrityError:
        # Another request queued one at the same moment.
        active = project.analyses.filter(status__in=WebsiteAnalysis.ACTIVE_STATUSES).first()
        raise AnalysisAlreadyRunning(active)


def claim_next_analysis():
    """Atomically move the oldest queued analysis to running and return it."""
    candidates = WebsiteAnalysis.objects.filter(status=WebsiteAnalysis.Status.QUEUED).order_by(
        "created_at", "id"
    ).values_list("pk", flat=True)[:5]
    for pk in candidates:
        claimed = WebsiteAnalysis.objects.filter(
            pk=pk, status=WebsiteAnalysis.Status.QUEUED
        ).update(status=WebsiteAnalysis.Status.RUNNING, started_at=timezone.now())
        if claimed:
            return WebsiteAnalysis.objects.get(pk=pk)
    return None


def fail_stale_analyses(now=None):
    """Mark analyses left running by a stopped worker as failed. Returns the count."""
    cutoff = (now or timezone.now()) - STALE_AFTER
    return WebsiteAnalysis.objects.filter(
        status=WebsiteAnalysis.Status.RUNNING, started_at__lt=cutoff
    ).update(
        status=WebsiteAnalysis.Status.FAILED,
        error_code="interrupted",
        error_message="The analysis was interrupted. Please start it again.",
        finished_at=timezone.now(),
    )


def _save_page(analysis, position, page):
    info = page.info
    AnalyzedPage.objects.create(
        analysis=analysis,
        position=position,
        url=page.url,
        status=page.status,
        http_status=page.http_status,
        depth=page.depth,
        error_code=page.error_code,
        error_message=page.error_message[:500],
        title=info.title if info else "",
        meta_description=info.meta_description if info else "",
        canonical_url=info.canonical_url if info else "",
        language=info.language if info else "",
        theme_color=info.theme_color if info else "",
        open_graph=info.open_graph if info else {},
        headings=info.headings if info else [],
        text=info.text if info else "",
        text_truncated=info.text_truncated if info else False,
        images=info.images if info else [],
        structured_data=info.structured_data if info else [],
        links=info.links if info else [],
        links_found=len(info.links) if info else 0,
    )


def run_analysis(analysis, crawl_function=None, **crawl_options):
    """Crawl the website and record the outcome. Never raises for website problems."""
    crawl_function = crawl_function or crawl
    position = 0
    attempted = 0
    succeeded = 0

    def on_page(page):
        nonlocal position, attempted, succeeded
        position += 1
        _save_page(analysis, position, page)
        if page.status != "skipped":
            attempted += 1
        if page.status == "success":
            succeeded += 1
        WebsiteAnalysis.objects.filter(pk=analysis.pk).update(
            pages_attempted=attempted, pages_succeeded=succeeded
        )

    try:
        result = crawl_function(
            analysis.start_url, max_pages=analysis.max_pages, on_page=on_page, **crawl_options
        )
    except Exception:
        logger.exception("Website analysis %s crashed", analysis.pk)
        analysis.status = WebsiteAnalysis.Status.FAILED
        analysis.error_code = "internal_error"
        analysis.error_message = "Something went wrong on our side. Please try again later."
    else:
        analysis.stopped_reason = result.stopped_reason
        pages = result.pages
        start_page = pages[0] if pages else None
        if succeeded == 0:
            analysis.status = WebsiteAnalysis.Status.FAILED
            if start_page and start_page.error_message:
                analysis.error_code = start_page.error_code
                analysis.error_message = start_page.error_message[:500]
            else:
                analysis.error_code = "no_pages"
                analysis.error_message = "No pages could be analyzed."
        elif any(page.status == "failed" for page in pages):
            analysis.status = WebsiteAnalysis.Status.PARTIAL
        else:
            analysis.status = WebsiteAnalysis.Status.COMPLETED

    analysis.pages_attempted = attempted
    analysis.pages_succeeded = succeeded
    analysis.finished_at = timezone.now()
    analysis.save()
    if analysis.status in (WebsiteAnalysis.Status.COMPLETED, WebsiteAnalysis.Status.PARTIAL):
        try:
            analysis_finished.send(sender=WebsiteAnalysis, analysis=analysis)
        except Exception:
            # A problem in a follow-up step must not undo a finished analysis.
            logger.exception("Post-analysis processing failed for analysis %s", analysis.pk)
    return analysis
