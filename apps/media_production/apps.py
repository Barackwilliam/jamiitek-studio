from django.apps import AppConfig
from django.db.models.signals import post_delete


class MediaProductionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_production"
    label = "media_production"

    def ready(self):
        from apps.core.worker import JobHandler, register

        from .jobs import claim_next_render, fail_stale_renders, run_render
        from .models import AudioTrack, VideoRender

        register(JobHandler(
            name="video rendering",
            claim=claim_next_render,
            run=run_render,
            fail_stale=fail_stale_renders,
            describe=lambda video: f"{video.aspect} {video.quality} video #{video.pk}",
        ))

        def delete_file(sender, instance, **kwargs):
            if instance.file:
                instance.file.delete(save=False)

        post_delete.connect(delete_file, sender=AudioTrack, dispatch_uid="audio.delete_file")
        post_delete.connect(delete_file, sender=VideoRender, dispatch_uid="videos.delete_file")
