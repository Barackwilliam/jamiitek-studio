from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "business_name", "owner", "updated_at"]
    list_select_related = ["owner"]
    search_fields = ["name", "business_name", "owner__username"]
    readonly_fields = ["created_at", "updated_at"]
