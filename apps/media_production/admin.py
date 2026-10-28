from django.contrib import admin

from .models import AudioTrack, VideoRender


@admin.register(VideoRender)
class VideoRenderAdmin(admin.ModelAdmin):
    list_display = ["__str__", "project", "status", "duration", "created_at"]
    list_filter = ["status", "quality", "aspect"]
    list_select_related = ["project"]
    readonly_fields = ["plan", "progress", "error_code", "error_message", "created_at", "started_at", "finished_at"]


@admin.register(AudioTrack)
class AudioTrackAdmin(admin.ModelAdmin):
    list_display = ["__str__", "project", "kind", "created_at"]
    list_filter = ["kind"]
