from django.urls import path

from . import views

app_name = "media_production"

urlpatterns = [
    path("", views.videos, name="videos"),
    path("new/", views.create_video, name="create"),
    path("<int:pk>/", views.video_detail, name="video"),
    path("<int:pk>/file/", views.video_file, name="video_file"),
    path("<int:pk>/delete/", views.video_delete, name="video_delete"),
    path("audio/upload/", views.upload_audio, name="upload_audio"),
    path("audio/<int:pk>/file/", views.audio_file, name="audio_file"),
    path("audio/<int:pk>/delete/", views.audio_delete, name="audio_delete"),
]
