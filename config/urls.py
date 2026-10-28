from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("projects/", include("apps.projects.urls")),
    path("projects/<int:project_pk>/analyses/", include("apps.website_analyzer.urls")),
    path("projects/<int:project_pk>/profile/", include("apps.business_profiles.urls")),
    path("projects/<int:project_pk>/content/", include("apps.marketing_content.urls")),
    path("", include("apps.core.urls")),
]
