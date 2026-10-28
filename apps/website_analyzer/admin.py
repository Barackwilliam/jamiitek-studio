from django.contrib import admin

from .models import AnalyzedPage, WebsiteAnalysis


class AnalyzedPageInline(admin.TabularInline):
    model = AnalyzedPage
    extra = 0
    fields = ["position", "url", "status", "http_status", "title", "error_code"]
    readonly_fields = fields
    can_delete = False


@admin.register(WebsiteAnalysis)
class WebsiteAnalysisAdmin(admin.ModelAdmin):
    list_display = ["start_url", "project", "status", "pages_succeeded", "pages_attempted", "created_at"]
    list_filter = ["status"]
    list_select_related = ["project"]
    readonly_fields = ["created_at", "started_at", "finished_at"]
    inlines = [AnalyzedPageInline]
