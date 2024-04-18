#!/usr/bin/env python

"""
Set environment variables by collecting secrets from AWS Secrets Manager

The secret ids should be in the environment

"""

import os
import logging

from .aws_secrets_manager_helpers import get_secret_string


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def set_ica_env_vars():
    os.environ["ICA_BASE_URL"] = os.environ.get("ICA_BASE_URL", "https://aps2.platform.illumina.com")
    os.environ["ICA_ACCESS_TOKEN"] = get_ica_access_token_from_aws_secrets_manager()


def get_ica_access_token_from_aws_secrets_manager():
    secret_id = os.environ.get("ICA_ACCESS_TOKEN_SECRET_ID", None)

    if secret_id is None:
        logger.error("ICA_ACCESS_TOKEN_SECRET_ID env var is not set")
        raise EnvironmentError

    return get_secret_string(secret_id)


def get_ica_tes_configuration():
    from libica.openapi.libtes import Configuration
    return Configuration(
        host=os.environ.get("ICA_BASE_URL"),
        api_key_prefix={
            "Authorization": "Bearer"
        },
        api_key={
            "Authorization": os.environ.get("ICA_ACCESS_TOKEN")
        }
    )


def get_ica_gds_configuration():
    from libica.openapi.libgds import Configuration
    return Configuration(
        host=os.environ.get("ICA_BASE_URL"),
        api_key={
            "Authorization": os.environ.get("ICA_ACCESS_TOKEN")
        },
        api_key_prefix={
            "Authorization": "Bearer"
        }
    )
