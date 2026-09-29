"""Isolated SQLite settings for automated tests and local verification."""

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("TEST_DATABASE_NAME", ":memory:"),  # noqa: F405
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SALE_EMAIL_ENABLED = True
DEFAULT_FROM_EMAIL = "serve@example.test"
