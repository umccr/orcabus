# -*- coding: utf-8 -*-
"""AWS Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=sequence_run_manager.settings.aws
"""
import copy
import json
import logging
from types import SimpleNamespace

from environ import Env
from libumccr.aws import libsm

from .base import *  # noqa

logger = logging.getLogger(__name__)

DEBUG = False

secret_id = os.environ.get("SECRET_ID")

try:
    secret_str = libsm.get_secret(secret_id)  # this will be lru cached throughout exec lifetime
    sd = json.loads(secret_str, object_hook=lambda d: SimpleNamespace(**d))
    db_conn = f"{sd.engine}://{sd.username}:{sd.password}@{sd.host}:{sd.port}/{sd.dbname}"
except Exception as e:
    logger.error(f"Error retrieving db secret from the Secret Manager: {e}")
    raise e

db_conn_cfg = Env.db_url_config(db_conn)

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
