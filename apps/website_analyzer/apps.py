from django.apps import AppConfig


class WebsiteAnalyzerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.website_analyzer"
    label = "website_analyzer"

    def ready(self):
        from apps.core.worker import JobHandler, register

        from .jobs import claim_next_analysis, fail_stale_analyses, run_analysis

        register(JobHandler(
            name="website analysis",
            claim=claim_next_analysis,
            run=run_analysis,
            fail_stale=fail_stale_analyses,
            describe=lambda analysis: f"{analysis.start_url} (#{analysis.pk})",
        ))
