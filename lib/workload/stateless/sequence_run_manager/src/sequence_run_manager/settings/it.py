# -*- coding: utf-8 -*-
"""integration tests Django settings

Usage:
- export DJANGO_SETTINGS_MODULE=sequence_run_manager.settings.it
"""
from environ import Env

from .base import *  # noqa

db_conn_cfg = Env.db_url_config(
    # pragma: allowlist nextline secret
    os.getenv("DB_URL", "mysql://root:root@localhost:3306/orcabus")
)

DATABASES = {"default": db_conn_cfg}
