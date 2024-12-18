# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=sequence_run_manager.settings.local
"""
import sys

from environ import Env

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sequence_run_manager',
        'USER': 'orcabus',
        'PASSWORD': 'orcabus',  # pragma: allowlist-secret
        'HOST': os.getenv('DB_HOSTNAME', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

INSTALLED_APPS += (
    "django_extensions",
    "drf_spectacular",
)

ROOT_URLCONF = "sequence_run_manager.urls.local"

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
    'CAMELIZE_NAMES': True,
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields',
        'drf_spectacular.hooks.postprocess_schema_enums'
    ],
}
