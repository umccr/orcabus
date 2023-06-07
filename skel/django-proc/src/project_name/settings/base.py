"""DO NOT USE base SETTING IN PRODUCTION"""
import os
import uuid
from pathlib import Path

import aws_xray_sdk
from corsheaders.defaults import default_headers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", uuid.uuid4())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", True)

DB_PREFIX = "{{project_name}}_"

INSTALLED_APPS = [
    "django_database_prefix",
    "django.contrib.contenttypes",
    "{{project_name}}",
    "aws_xray_sdk.ext.django",
]

MIDDLEWARE = [
    "aws_xray_sdk.ext.django.middleware.XRayMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---

# 1GB packet limit for MySQL. See https://dev.mysql.com/doc/refman/5.7/en/packet-too-large.html
MYSQL_CLIENT_MAX_ALLOWED_PACKET = 1073741824

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}

XRAY_RECORDER = {
    "AUTO_INSTRUMENT": True,
    "AWS_XRAY_CONTEXT_MISSING": os.getenv("AWS_XRAY_CONTEXT_MISSING", "LOG_ERROR"),
    "AWS_XRAY_TRACING_NAME": os.getenv("AWS_XRAY_TRACING_NAME", "{{project_name}}"),
}

# turn off xray more generally and, you can overwrite with env var AWS_XRAY_SDK_ENABLED=true at runtime
aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)
