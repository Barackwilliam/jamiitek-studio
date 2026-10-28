"""
Django settings for JamiiTek AI Marketing Studio.

All environment-specific values come from environment variables. For local
development, copy `.env.example` to `.env` and adjust it; real environment
variables always take precedence over values in `.env`.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value, got {value!r}.")


def env_list(name, default=()):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def env_path(name, default):
    value = os.environ.get(name, "").strip()
    return Path(value) if value else default


# Core security
# ------------------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false."
        )
    # Only ever used for local development with DEBUG enabled.
    SECRET_KEY = "django-insecure-local-development-only"

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"] if DEBUG else [],
)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# Applications
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.accounts",
    "apps.projects",
    "apps.website_analyzer",
    "apps.business_profiles",
    "apps.marketing_content",
    "apps.creative_assets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
# ------------------------------------------------------------------------------
# DATABASE_URL selects PostgreSQL, for example Supabase (DEC-018). Without it,
# a local SQLite file is used, which keeps tests and offline work free and
# independent of any hosted quota.

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", "60")),
            conn_health_checks=True,
            ssl_require=env_bool("DJANGO_DB_SSL_REQUIRE", default=True),
        )
    }
    if env_bool("DJANGO_DB_TRANSACTION_POOLER", default=False):
        # Supabase's transaction pooler (port 6543) cannot keep server-side
        # cursors or prepared statements between transactions.
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
        DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env_path("DJANGO_SQLITE_PATH", BASE_DIR / "db.sqlite3"),
        }
    }

# On PostgreSQL, row level security is enabled on every table after each
# migration so Supabase's Data API cannot read Django's tables (DEC-018).
POSTGRES_ENABLE_RLS = env_bool("DJANGO_DB_ENABLE_RLS", default=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication
# ------------------------------------------------------------------------------

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "projects:list"
LOGOUT_REDIRECT_URL = "core:home"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# ------------------------------------------------------------------------------
# English and Kiswahili are the proposed initial languages (OPEN-002).

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("sw", "Kiswahili"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Africa/Dar_es_Salaam")
USE_I18N = True
USE_TZ = True


# Static and media files
# ------------------------------------------------------------------------------
# Media holds user uploads and generated files. It must never be committed and
# should point outside the repository in shared or hosted environments.

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = env_path("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")

MEDIA_URL = "media/"
MEDIA_ROOT = env_path("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

# Uploaded, imported and generated files are private. They are never served
# from MEDIA_URL; the application streams them after checking ownership.
# With STORAGE_S3_BUCKET set, files go to an S3-compatible bucket such as a
# private Supabase Storage bucket (DEC-018); otherwise to MEDIA_ROOT.
STORAGE_S3_BUCKET = os.environ.get("STORAGE_S3_BUCKET", "").strip()

if STORAGE_S3_BUCKET:
    _default_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": STORAGE_S3_BUCKET,
            "endpoint_url": os.environ.get("STORAGE_S3_ENDPOINT_URL", "").strip() or None,
            "region_name": os.environ.get("STORAGE_S3_REGION", "").strip() or None,
            "access_key": os.environ.get("STORAGE_S3_ACCESS_KEY_ID", "").strip(),
            "secret_key": os.environ.get("STORAGE_S3_SECRET_ACCESS_KEY", "").strip(),
            "addressing_style": "path",
            "signature_version": "s3v4",
            "default_acl": None,
            "file_overwrite": False,
            "querystring_auth": True,
        },
    }
else:
    _default_storage = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

STORAGES = {
    "default": _default_storage,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Largest image a user may upload or import.
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))


# HTTPS and cookie security for non-debug environments
# ------------------------------------------------------------------------------

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
    )
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
    if env_bool("DJANGO_TRUST_PROXY_SSL_HEADER", default=False):
        # Only enable behind a proxy that always sets this header.
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True


# AI text generation (DEC-021)
# ------------------------------------------------------------------------------
# Any service with an OpenAI-compatible chat completions API. Leave empty to
# disable AI features. The key is a secret and must never reach the browser.

AI_TEXT_PROVIDER_NAME = os.environ.get("AI_TEXT_PROVIDER_NAME", "").strip() or "AI service"
AI_TEXT_BASE_URL = os.environ.get("AI_TEXT_BASE_URL", "").strip()
AI_TEXT_API_KEY = os.environ.get("AI_TEXT_API_KEY", "").strip()
AI_TEXT_MODEL = os.environ.get("AI_TEXT_MODEL", "").strip()
AI_TEXT_TIMEOUT = float(os.environ.get("AI_TEXT_TIMEOUT", "60"))
AI_TEXT_JSON_MODE = env_bool("AI_TEXT_JSON_MODE", default=True)
# Shown to users before their business information is sent to the provider.
AI_TEXT_DATA_NOTICE = os.environ.get("AI_TEXT_DATA_NOTICE", "").strip()


# Logging
# ------------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}
