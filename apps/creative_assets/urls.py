from django.urls import path, re_path

from . import views

app_name = "creative_assets"

urlpatterns = [
    path("", views.library, name="library"),
    path("upload/", views.upload, name="upload"),
    path("import/", views.import_from_website, name="import"),
    re_path(r"^images/(?P<pk>\d+)/(?P<variant>full|thumb)/$", views.asset_file, name="asset_file"),
    path("images/<int:pk>/delete/", views.asset_delete, name="asset_delete"),
    path("posters/new/", views.poster_create, name="poster_create"),
    path("posters/<int:pk>/", views.poster_detail, name="poster"),
    path("posters/<int:pk>/file/", views.poster_file, name="poster_file"),
    path("posters/<int:pk>/delete/", views.poster_delete, name="poster_delete"),
]
