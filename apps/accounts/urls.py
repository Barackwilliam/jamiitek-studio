from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import RateLimitedAuthenticationForm

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            redirect_authenticated_user=True, authentication_form=RateLimitedAuthenticationForm
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
