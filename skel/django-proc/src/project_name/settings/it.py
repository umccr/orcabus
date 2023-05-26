# -*- coding: utf-8 -*-
"""integration tests Django settings

Usage:
- export DJANGO_SETTINGS_MODULE={{project_name}}.settings.it
"""
from environ import Env

from .base import *  # noqa

# pragma: allowlist nextline secret
db_conn_cfg = Env.db_url_config(
    os.getenv("DB_URL", "mysql://root:root@localhost:3306/orcabus")  # pragma: allowlist secret
)

DATABASES = {"default": db_conn_cfg}
