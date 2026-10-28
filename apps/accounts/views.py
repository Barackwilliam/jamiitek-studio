from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.core import ratelimit

SIGNUP_WINDOW = timedelta(hours=1)
SIGNUP_LIMIT_PER_IP = 10


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("projects:list")
    form = UserCreationForm(request.POST or None)
    status = 200
    if request.method == "POST":
        ip = ratelimit.client_ip(request)
        if ratelimit.is_limited("signup-ip", ip, SIGNUP_LIMIT_PER_IP, SIGNUP_WINDOW):
            form.add_error(None, _("Too many sign-up attempts from your network. Please try again later."))
            status = 429
        else:
            ratelimit.record("signup-ip", ip)
            if form.is_valid():
                user = form.save()
                login(request, user)
                return redirect("projects:list")
    return render(request, "accounts/signup.html", {"form": form}, status=status)
