"""Queuing and running AI generation jobs.

Only facts the user confirmed (DEC-020) are sent to the AI. The output is
validated and checked for unsupported claims before it is stored as a
draft. Provider failures are recorded with a user-safe message and never
lose the user's brief or earlier drafts.
"""

import logging
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone, translation
from django.utils.translation import gettext_noop

from apps.business_profiles.models import FactKey, ProfileFact
from integrations.ai import ProviderError, TextGenerationRequest
from integrations.ai.registry import get_text_provider

from . import prompts
from .models import ContentDraft, GenerationJob
from .validation import (
    InvalidOutput,
    clean_concepts,
    clean_script,
    concept_texts,
    find_unsupported_claims,
    parse_json_object,
    script_texts,
)

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=10)
INVALID_OUTPUT_ATTEMPTS = 2


class GenerationAlreadyRunning(Exception):
    def __init__(self, job):
        super().__init__("A generation job is already queued or running for this brief.")
        self.job = job


def confirmed_facts(project):
    """Snapshot of the project's confirmed facts with stable references."""
    facts = ProfileFact.objects.filter(
        profile__project=project, status=ProfileFact.Status.CONFIRMED
    ).order_by("key", "id")
    # Stored and sent to the AI in English, whatever the user's language;
    # templates translate the label when showing it.
    with translation.override("en"):
        labels = {key: str(label) for key, label in FactKey.choices}
    return [
        {"ref": f"F{index}", "fact_id": fact.pk, "key": fact.key,
         "label": labels.get(fact.key, fact.key), "value": fact.value}
        for index, fact in enumerate(facts, start=1)
    ]


def _queue(brief, kind, concept=None):
    active = brief.jobs.filter(status__in=GenerationJob.ACTIVE_STATUSES).first()
    if active:
        raise GenerationAlreadyRunning(active)
    try:
        with transaction.atomic():
            return GenerationJob.objects.create(brief=brief, kind=kind, concept=concept)
    except IntegrityError:
        raise GenerationAlreadyRunning(brief.jobs.filter(status__in=GenerationJob.ACTIVE_STATUSES).first())


def request_concepts(brief):
    return _queue(brief, GenerationJob.Kind.CONCEPTS)


def request_script(brief, concept):
    if concept.brief_id != brief.pk or concept.kind != ContentDraft.Kind.CONCEPT:
        raise ValueError("concept does not belong to this brief")
    return _queue(brief, GenerationJob.Kind.SCRIPT, concept=concept)


def claim_next_job():
    candidates = GenerationJob.objects.filter(status=GenerationJob.Status.QUEUED).order_by(
        "created_at", "id").values_list("pk", flat=True)[:5]
    for pk in candidates:
        if GenerationJob.objects.filter(pk=pk, status=GenerationJob.Status.QUEUED).update(
            status=GenerationJob.Status.RUNNING, started_at=timezone.now()
        ):
            return GenerationJob.objects.select_related("brief__project", "concept").get(pk=pk)
    return None


def fail_stale_jobs():
    return GenerationJob.objects.filter(
        status=GenerationJob.Status.RUNNING, started_at__lt=timezone.now() - STALE_AFTER
    ).update(
        status=GenerationJob.Status.FAILED,
        error_code="interrupted",
        error_message=gettext_noop("Writing was interrupted. Please try again."),
        finished_at=timezone.now(),
    )


def _unknown_reference_flags(unknown):
    if not unknown:
        return []
    return [{
        "code": "unknown_reference",
        "location": "fact references",
        "text": ", ".join(sorted(set(unknown))),
        "message": gettext_noop("The AI referred to information that is not in your confirmed facts. Check the text carefully."),
    }]


def _generate(provider, request, clean):
    """Call the provider, retrying once if the answer cannot be used."""
    last_error = None
    for _attempt in range(INVALID_OUTPUT_ATTEMPTS):
        result = provider.generate(request)
        try:
            return result, clean(parse_json_object(result.text))
        except InvalidOutput as exc:
            logger.warning("Unusable AI output (%s) from %s", exc, provider.name)
            last_error = exc
    raise last_error


def run_job(job, provider=None):
    """Run one claimed job and store its drafts. Never raises for expected failures."""
    brief = job.brief
    facts = confirmed_facts(brief.project)
    known_refs = {fact["ref"] for fact in facts}
    try:
        if not facts:
            job.error_code = "no_facts"
            job.error_message = gettext_noop("There is no confirmed business information yet. "
                                              "Confirm or add information in the business profile first.")
            raise _JobFailed()
        provider = provider or get_text_provider()
        if job.kind == GenerationJob.Kind.CONCEPTS:
            request = TextGenerationRequest(
                system_prompt=prompts.SYSTEM_PROMPT,
                user_prompt=prompts.concepts_prompt(brief, facts),
                temperature=0.9,
            )
            result, (concepts, unknown) = _generate(
                provider, request, lambda data: clean_concepts(data, known_refs))
            for concept in concepts:
                ContentDraft.objects.create(
                    brief=brief, job=job, kind=ContentDraft.Kind.CONCEPT, data=concept, facts=facts,
                    flags=find_unsupported_claims(concept_texts(concept), facts)
                    + _unknown_reference_flags(unknown),
                    provider=result.provider, model=result.model,
                    prompt_version=prompts.PROMPT_VERSION,
                )
        else:
            concept = {k: v for k, v in job.concept.data.items() if k != "fact_ids"}
            request = TextGenerationRequest(
                system_prompt=prompts.SYSTEM_PROMPT,
                user_prompt=prompts.script_prompt(brief, facts, concept),
                temperature=0.7,
            )
            result, (script, unknown) = _generate(
                provider, request, lambda data: clean_script(data, known_refs))
            ContentDraft.objects.create(
                brief=brief, job=job, kind=ContentDraft.Kind.SCRIPT, concept=job.concept,
                data=script, facts=facts,
                flags=find_unsupported_claims(script_texts(script), facts)
                + _unknown_reference_flags(unknown),
                provider=result.provider, model=result.model,
                prompt_version=prompts.PROMPT_VERSION,
            )
        job.status = GenerationJob.Status.COMPLETED
        job.provider, job.model, job.usage = result.provider, result.model, result.usage
    except _JobFailed:
        job.status = GenerationJob.Status.FAILED
    except ProviderError as exc:
        job.status = GenerationJob.Status.FAILED
        job.error_code, job.error_message = exc.code, exc.message
    except InvalidOutput:
        job.status = GenerationJob.Status.FAILED
        job.error_code = "bad_output"
        job.error_message = gettext_noop("The AI's answer could not be used. Please try again.")
    except Exception:
        logger.exception("Generation job %s crashed", job.pk)
        job.status = GenerationJob.Status.FAILED
        job.error_code = "internal_error"
        job.error_message = gettext_noop("Something went wrong on our side. Please try again later.")
    job.finished_at = timezone.now()
    job.save()
    return job


class _JobFailed(Exception):
    pass
