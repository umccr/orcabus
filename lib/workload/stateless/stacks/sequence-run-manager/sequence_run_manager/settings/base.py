"""DO NOT USE base SETTING IN PRODUCTION"""
import os
import uuid
from pathlib import Path

import aws_xray_sdk
from corsheaders.defaults import default_headers

API_VERSION = "v1"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", uuid.uuid4())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", True)

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "sequence_run_manager",
    "aws_xray_sdk.ext.django",
    "drf_spectacular",
]

MIDDLEWARE = [
    "aws_xray_sdk.ext.django.middleware.XRayMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "djangorestframework_camel_case.middleware.CamelCaseMiddleWare",
]

ROOT_URLCONF = "sequence_run_manager.urls.base"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sequence_run_manager.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---

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

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # https://www.django-rest-framework.org/api-guide/parsers/#camelcase-json
    # https://github.com/vbabiy/djangorestframework-camel-case
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "JSON_UNDERSCOREIZE": {
        'no_underscore_before_number': True,
    },
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-amz-security-token",
    "x-amz-date",
    "Content-Disposition",
]

XRAY_RECORDER = {
    "AUTO_INSTRUMENT": True,
    "AWS_XRAY_CONTEXT_MISSING": os.getenv("AWS_XRAY_CONTEXT_MISSING", "LOG_ERROR"),
    "AWS_XRAY_TRACING_NAME": os.getenv("AWS_XRAY_TRACING_NAME", "sequence_run_manager"),
}

# turn off xray more generally and, you can overwrite with env var AWS_XRAY_SDK_ENABLED=true at runtime
aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)

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
    'COMPONENT_SPLIT_REQUEST': True
}
