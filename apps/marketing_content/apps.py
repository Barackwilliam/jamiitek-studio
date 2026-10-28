from django.apps import AppConfig


class MarketingContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.marketing_content"
    label = "marketing_content"

    def ready(self):
        from apps.core.worker import JobHandler, register

        from .generation import claim_next_job, fail_stale_jobs, run_job

        register(JobHandler(
            name="AI writing",
            claim=claim_next_job,
            run=run_job,
            fail_stale=fail_stale_jobs,
            describe=lambda job: f"{job.get_kind_display().lower()} for brief #{job.brief_id}",
        ))
