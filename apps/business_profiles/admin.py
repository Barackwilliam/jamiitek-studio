from django.contrib import admin

from .models import BusinessProfile, ProfileFact


class ProfileFactInline(admin.TabularInline):
    model = ProfileFact
    extra = 0
    fields = ["key", "value", "source", "status", "edited_by_user"]
    readonly_fields = ["source", "edited_by_user"]


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ["project", "updated_at"]
    list_select_related = ["project"]
    inlines = [ProfileFactInline]
