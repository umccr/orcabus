# -*- coding: utf-8 -*-
"""AWS Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=sequence_run_manager.settings.aws
"""
import copy

from environ import Env
from libumccr.aws import libssm

from .base import *  # noqa

SECRET_KEY = libssm.get_secret("/orcabus/backend/django_secret_key")

DEBUG = False

db_conn_cfg = Env.db_url_config(libssm.get_secret("/orcabus/backend/full_db_url"))

DATABASES = {"default": db_conn_cfg}

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = False

# FIXME: https://github.com/umccr/infrastructure/issues/272
CORS_ALLOWED_ORIGINS = [
    "https://portal.umccr.org",
    "https://portal.prod.umccr.org",
    "https://portal.stg.umccr.org",
    "https://portal.dev.umccr.org",
    "https://data.umccr.org",
    "https://data.prod.umccr.org",
    "https://data.dev.umccr.org",
    "https://data.stg.umccr.org",
]

CSRF_TRUSTED_ORIGINS = copy.deepcopy(CORS_ALLOWED_ORIGINS)
