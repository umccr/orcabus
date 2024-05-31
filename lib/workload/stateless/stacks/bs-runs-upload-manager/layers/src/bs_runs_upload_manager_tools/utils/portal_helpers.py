#!/usr/bin/env python

# Standard imports
import os
import logging
import json

# Local imports
from bs_runs_upload_manager_tools.utils.aws_secrets_manager_helpers import get_secret_string
from bs_runs_upload_manager_tools.utils.aws_ssm_helpers import get_ssm_parameter_value


# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_portal_token():
    os.environ["PORTAL_TOKEN"] = get_portal_token_from_aws_secrets_manager()


def set_api_url():
    os.environ["PORTAL_API_URL"] = get_api_url_from_ssm_parameter()


def get_portal_token_from_aws_secrets_manager():
    secret_id = os.environ.get("PORTAL_TOKEN_SECRET_ID", None)

    if secret_id is None:
        logger.error("PORTAL_TOKEN_SECRET_ID env var is not set")
        raise EnvironmentError

    return json.loads(get_secret_string(secret_id))['id_token']


def get_api_url_from_ssm_parameter():
    ssm_parameter_name = os.environ.get("PORTAL_API_URL_PARAMETER_NAME", None)

    if ssm_parameter_name is None:
        logger.error("API_URL_PARAMETER_NAME env var is not set")
        raise EnvironmentError

    return get_ssm_parameter_value(ssm_parameter_name)
