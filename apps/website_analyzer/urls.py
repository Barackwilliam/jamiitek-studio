from django.urls import path

from . import views

app_name = "website_analyzer"

urlpatterns = [
    path("start/", views.start_analysis, name="start"),
    path("<int:pk>/", views.analysis_detail, name="detail"),
]
