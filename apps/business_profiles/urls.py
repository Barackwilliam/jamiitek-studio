from django.urls import path

from . import views

app_name = "business_profiles"

urlpatterns = [
    path("", views.profile_detail, name="detail"),
    path("refresh/", views.refresh_from_analysis, name="refresh"),
    path("facts/add/", views.add_fact, name="add_fact"),
    path("facts/<int:pk>/status/", views.set_fact_status, name="set_status"),
    path("facts/<int:pk>/edit/", views.edit_fact, name="edit_fact"),
]
