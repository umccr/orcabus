# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=workflow_manager.settings.local
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
    "drf_spectacular",
)

ROOT_URLCONF = "workflow_manager.urls.local"

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = sys.maxsize

# --- drf-spectacular settings

REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

SPECTACULAR_SETTINGS = {
    'TITLE': 'UMCCR OrcaBus sequence_run_manager API',
    'DESCRIPTION': 'UMCCR OrcaBus sequence_run_manager API',
    'VERSION': API_VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'SECURITY': [
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    ],
    'CONTACT': {
        'name': 'UMCCR',
        'email': 'services@umccr.org'
    },
    "LICENSE": {
        "name": "MIT License",
    },
    "EXTERNAL_DOCS": {
        "description": "Terms of service",
        "url": "https://umccr.org/",
    },
}
