# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=library_manager.settings.local
"""
import sys

from environ import Env

from .base import *  # noqa

# pragma: allowlist nextline secret
db_conn_cfg = Env.db_url_config(
    os.getenv(
        "DB_URL", "mysql://root:root@localhost:3306/orcabus"  # pragma: allowlist secret
    )
)
db_conn_cfg["OPTIONS"] = {
    "max_allowed_packet": MYSQL_CLIENT_MAX_ALLOWED_PACKET,
}

DATABASES = {"default": db_conn_cfg}

INSTALLED_APPS += (
    "django_extensions",
    "drf_yasg",
)

ROOT_URLCONF = "library_manager.urls.local"

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
