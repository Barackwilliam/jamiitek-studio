"""Tests for environment-driven settings.

Settings are evaluated once per process, so production-like configurations
are checked in a separate Python process with a controlled environment.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import env_bool, env_list

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PRODUCTION_ENV = {
    "DJANGO_DEBUG": "False",
    "DJANGO_SECRET_KEY": "test-only-" + "x" * 60,
    "DJANGO_ALLOWED_HOSTS": "studio.example.com",
}


def run_manage(args, env_overrides):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("DJANGO_")
    }
    # Explicit values (including empty strings) stop a developer's local
    # .env file from leaking into these checks.
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_DEBUG": "",
            "DJANGO_SECRET_KEY": "",
            "DJANGO_ALLOWED_HOSTS": "",
        }
    )
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


class EnvHelperTests(SimpleTestCase):
    def test_env_bool_accepts_common_values(self):
        for raw, expected in [("true", True), ("1", True), ("Yes", True),
                              ("false", False), ("0", False), ("off", False)]:
            with self.subTest(raw=raw), mock.patch.dict(os.environ, {"FLAG": raw}):
                self.assertIs(env_bool("FLAG"), expected)

    def test_env_bool_uses_default_when_missing_or_empty(self):
        with mock.patch.dict(os.environ, {"FLAG": ""}):
            self.assertIs(env_bool("FLAG", default=True), True)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIs(env_bool("FLAG"), False)

    def test_env_bool_rejects_ambiguous_values(self):
        with mock.patch.dict(os.environ, {"FLAG": "maybe"}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool("FLAG")

    def test_env_list_splits_and_strips(self):
        with mock.patch.dict(os.environ, {"HOSTS": " a.com, ,b.com "}):
            self.assertEqual(env_list("HOSTS"), ["a.com", "b.com"])


class ProductionSettingsTests(SimpleTestCase):
    def test_missing_secret_key_is_refused_when_debug_is_off(self):
        result = run_manage(["check"], {"DJANGO_DEBUG": "False"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_debug_defaults_to_off(self):
        result = run_manage(["check"], {})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_production_configuration_passes_deployment_checks(self):
        # HSTS for subdomains (W005) and browser preloading (W021) depend on
        # the real domain, so they are opt-in settings. Every other deployment
        # warning must be absent.
        domain_owner_decisions = {"security.W005", "security.W021"}

        result = run_manage(["check", "--deploy"], PRODUCTION_ENV)
        output = result.stdout + result.stderr
        reported = set(re.findall(r"\((\w+\.[EW]\d+)\)", output))

        self.assertEqual(result.returncode, 0, msg=output)
        self.assertLessEqual(reported, domain_owner_decisions, msg=output)

    def test_hsts_opt_ins_clear_remaining_deployment_warnings(self):
        result = run_manage(
            ["check", "--deploy", "--fail-level", "WARNING"],
            {
                **PRODUCTION_ENV,
                "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS": "True",
                "DJANGO_SECURE_HSTS_PRELOAD": "True",
            },
        )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
