#!/usr/bin/env python3

"""
Use low-level pyriandx commands
"""

from pyriandx.client import Client
from os import environ
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_pieriandx_client(
    email: str = environ.get("PIERIANDX_USER_EMAIL", None),
    token: str = environ.get("PIERIANDX_USER_AUTH_TOKEN", None),
    instiution: str = environ.get("PIERIANDX_INSTITUTION", None),
    base_url: str = environ.get("PIERIANDX_BASE_URL", None)
) -> Client:
    """
    Get the pieriandx client, validate environment variables
    PIERIANDX_BASE_URL
    PIERIANDX_INSTITUTION
    PIERIANDX_USER_EMAIL
    PIERIANDX_USER_AUTH_TOKEN
    :return:
    """

    missing_env_vars = False

    # Check inputs
    if email is None:
        logger.error(f"Please set the environment variable 'PIERIANDX_USER_EMAIL'")
        missing_env_vars = True
    if token is None:
        logger.error(f"Please set the environment variable 'PIERIANDX_USER_AUTH_TOKEN'")
        missing_env_vars = True
    if instiution is None:
        logger.error(f"Please set the environment variable 'PIERIANDX_INSTITUTION'")
        missing_env_vars = True
    if base_url is None:
        logger.error(f"Please set the environment variable 'PIERIANDX_BASE_URL'")
        missing_env_vars = True

    if missing_env_vars:
        logger.error("Missing PIERIANDX environment variable")
        raise EnvironmentError

    # Return client object
    return Client(
        email=email,
        key=token,
        institution=instiution,
        base_url=base_url,
        key_is_auth_token=True
    )
