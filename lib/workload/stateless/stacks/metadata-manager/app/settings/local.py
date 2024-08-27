# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=app.settings.local
"""
import sys

from environ import Env

from .base import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'metadata_manager',
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

ROOT_URLCONF = "app.urls.local"

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = sys.maxsize

REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

SPECTACULAR_SETTINGS = {
    'TITLE': 'Metadata Manager API',
    'DESCRIPTION': 'The Metadata Manager API for UMCCR.',
    'VERSION': '0.0.1',
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
