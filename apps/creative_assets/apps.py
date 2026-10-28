from django.apps import AppConfig
from django.db.models.signals import post_delete


class CreativeAssetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.creative_assets"
    label = "creative_assets"

    def ready(self):
        from apps.core.worker import JobHandler, register

        from .importing import claim_next_import, fail_stale_imports, run_import
        from .models import Asset, Poster

        register(JobHandler(
            name="image import",
            claim=claim_next_import,
            run=run_import,
            fail_stale=fail_stale_imports,
            describe=lambda job: f"{len(job.urls)} image(s) for project #{job.project_id}",
        ))

        # Remove stored files when their rows are deleted, including when a
        # whole project is deleted, so private files are not left behind.
        def delete_asset_files(sender, instance, **kwargs):
            instance.delete_files()

        def delete_poster_file(sender, instance, **kwargs):
            if instance.file:
                instance.file.delete(save=False)

        post_delete.connect(delete_asset_files, sender=Asset, dispatch_uid="assets.delete_files")
        post_delete.connect(delete_poster_file, sender=Poster, dispatch_uid="posters.delete_file")
