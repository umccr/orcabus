#!/usr/bin/env python
import os

from bs_runs_upload_manager_tools.utils.aws_secrets_manager_helpers import get_secret_string

import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def set_portal_token():
    os.environ["PORTAL_TOKEN"] = get_portal_token_from_aws_secrets_manager()


def get_portal_token_from_aws_secrets_manager():
    secret_id = os.environ.get("PORTAL_TOKEN_SECRET_ID", None)

    if secret_id is None:
        logger.error("PORTAL_TOKEN_SECRET_ID env var is not set")
        raise EnvironmentError

    return get_secret_string(secret_id)


def get_api_url():
    return os.environ.get("API_URL", "https://api.sscheck.dev.umccr.org")


