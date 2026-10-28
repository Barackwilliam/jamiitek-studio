from django.contrib import admin

from .models import ContentDraft, GenerationJob, MarketingBrief


@admin.register(MarketingBrief)
class MarketingBriefAdmin(admin.ModelAdmin):
    list_display = ["project", "objective", "platform", "language", "created_at"]
    list_select_related = ["project"]


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ["brief", "kind", "status", "provider", "model", "created_at"]
    list_filter = ["status", "kind"]
    readonly_fields = ["usage", "created_at", "started_at", "finished_at"]


@admin.register(ContentDraft)
class ContentDraftAdmin(admin.ModelAdmin):
    list_display = ["__str__", "kind", "status", "brief", "created_at"]
    list_filter = ["kind", "status"]
