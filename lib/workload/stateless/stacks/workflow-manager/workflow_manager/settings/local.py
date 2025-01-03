# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=workflow_manager.settings.local
"""
import sys

from environ import Env

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'workflow_manager',
        'USER': 'orcabus',
        'PASSWORD': 'orcabus',  # pragma: allowlist-secret
        'HOST': os.getenv('DB_HOSTNAME', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

INSTALLED_APPS += (
    "django_extensions",
)

ROOT_URLCONF = "workflow_manager.urls.local"

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = sys.maxsize

