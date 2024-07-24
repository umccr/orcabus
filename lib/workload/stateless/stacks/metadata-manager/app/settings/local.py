# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=app.settings.local
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

ROOT_URLCONF = "app.urls.local"

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = sys.maxsize

REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

SPECTACULAR_SETTINGS = {
    'TITLE': 'Metadata Manager API',
    'DESCRIPTION': 'The Metadata Manager API for UMCCR.',
    'VERSION': '0.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
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
}

REDOC_SETTINGS = {
    "LAZY_RENDERING": False,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'django.db.backends.schema': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
