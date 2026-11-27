"""Banco SQLite isolado para executar o MVP local sem alterar PostgreSQL."""

from .test_settings import *  # noqa: F403

DEMO_REPORT_DIR = BASE_DIR / "reports"  # noqa: F405
DEMO_REPORT_DIR.mkdir(parents=True, exist_ok=True)
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(BASE_DIR / "reports" / "mga-demo.sqlite3")}}  # noqa: F405
