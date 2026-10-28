from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("apps.accounts.urls")),
    path("projects/", include("apps.projects.urls")),
    path("projects/<int:project_pk>/analyses/", include("apps.website_analyzer.urls")),
    path("projects/<int:project_pk>/profile/", include("apps.business_profiles.urls")),
    path("projects/<int:project_pk>/content/", include("apps.marketing_content.urls")),
    path("projects/<int:project_pk>/media/", include("apps.creative_assets.urls")),
    path("projects/<int:project_pk>/videos/", include("apps.media_production.urls")),
    path("", include("apps.core.urls")),
]
