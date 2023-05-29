# -*- coding: utf-8 -*-
"""local development Django settings

Usage:
- export DJANGO_SETTINGS_MODULE={{project_name}}.settings.local
"""

from environ import Env

from .base import *  # noqa

# pragma: allowlist nextline secret
db_conn_cfg = Env.db_url_config(
    os.getenv("DB_URL", "mysql://root:root@localhost:3306/orcabus")  # pragma: allowlist secret
)
db_conn_cfg["OPTIONS"] = {
    "max_allowed_packet": MYSQL_CLIENT_MAX_ALLOWED_PACKET,
}

DATABASES = {"default": db_conn_cfg}

INSTALLED_APPS += (
    "django_extensions",
)
