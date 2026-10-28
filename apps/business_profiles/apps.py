from django.apps import AppConfig


class BusinessProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.business_profiles"
    label = "business_profiles"

    def ready(self):
        from apps.website_analyzer.signals import analysis_finished

        from .suggestions import refresh_suggestions_after_analysis

        analysis_finished.connect(
            refresh_suggestions_after_analysis, dispatch_uid="business_profiles.refresh"
        )
