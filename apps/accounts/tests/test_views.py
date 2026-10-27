from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "neema", "password1": "Kilimanjaro-2026!", "password2": "Kilimanjaro-2026!"},
        )

        self.assertRedirects(response, reverse("projects:list"))
        self.assertTrue(get_user_model().objects.filter(username="neema").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]),
                         get_user_model().objects.get(username="neema").pk)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            reverse("signup"), {"username": "neema", "password1": "12345678", "password2": "12345678"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="neema").exists())

    def test_logged_in_user_is_redirected_away_from_signup(self):
        self.client.force_login(get_user_model().objects.create_user("juma", password="x-pass-123!"))

        response = self.client.get(reverse("signup"))

        self.assertRedirects(response, reverse("projects:list"))


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("juma", password="Correct-horse-9")

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"), {"username": "juma", "password": "Correct-horse-9"}
        )

        self.assertRedirects(response, reverse("projects:list"))

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(reverse("login"), {"username": "juma", "password": "wrong"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            reverse("login") + "?next=https://evil.example/",
            {"username": "juma", "password": "Correct-horse-9", "next": "https://evil.example/"},
        )

        self.assertRedirects(response, reverse("projects:list"))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)
