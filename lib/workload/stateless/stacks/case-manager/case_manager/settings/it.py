# -*- coding: utf-8 -*-
"""integration tests Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=case_manager.settings.it
"""
from environ import Env

from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'case_manager',
        'USER': 'orcabus',
        'PASSWORD': 'orcabus',  # pragma: allowlist-secret
        'HOST': os.getenv('DB_HOSTNAME', 'localhost'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}
