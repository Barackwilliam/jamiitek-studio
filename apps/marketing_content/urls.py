from django.urls import path

from . import views

app_name = "marketing_content"

urlpatterns = [
    path("", views.content_home, name="home"),
    path("briefs/new/", views.brief_create, name="brief_create"),
    path("briefs/<int:pk>/", views.brief_detail, name="brief"),
    path("briefs/<int:pk>/concepts/", views.regenerate_concepts, name="regenerate_concepts"),
    path("concepts/<int:pk>/script/", views.write_script, name="write_script"),
    path("scripts/<int:pk>/", views.script_detail, name="script"),
    path("scripts/<int:pk>/edit/", views.script_edit, name="script_edit"),
    path("scripts/<int:pk>/approve/", views.script_approve, name="script_approve"),
]
