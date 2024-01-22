# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=sequence_run_manager.settings.local
"""
import sys

from environ import Env

from .base import *  # noqa

db_conn_cfg = Env.db_url_config(
    # pragma: allowlist nextline secret
    os.getenv("DB_URL", "postgresql://orcabus:orcabus@localhost:5432/orcabus")
)

DATABASES = {"default": db_conn_cfg}

INSTALLED_APPS += (
    "django_extensions",
    "drf_yasg",
)

ROOT_URLCONF = "sequence_run_manager.urls.local"

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = sys.maxsize

# --- drf_yasg swagger and redoc settings

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
    "USE_SESSION_AUTH": False,
}

REDOC_SETTINGS = {
    "LAZY_RENDERING": False,
}
