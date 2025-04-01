#!/usr/bin/env python3
from typing import Dict, Optional, List, Union
from urllib.parse import urlunparse, urlparse

# Standard imports
import requests
import logging
from copy import deepcopy

from requests import HTTPError

# Locals
from .globals import (
    FASTQ_SUBDOMAIN_NAME,
)

from .aws_helpers import (
    get_orcabus_token, get_hostname
)

# Set default request params
DEFAULT_REQUEST_PARAMS = {}

# Set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_url(endpoint: str) -> str:
    """
    Get the URL for the Metadata endpoint
    :param endpoint:
    :return:
    """
    # Get the hostname
    hostname = get_hostname()

    return urlunparse(
        [
            "https",
            ".".join([FASTQ_SUBDOMAIN_NAME, hostname]),
            endpoint,
            None, None, None
        ]
    )


def get_request_response(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Run get response against the Metadata endpoint
    :param endpoint:
    :param params:
    :return:
    """
    # Get authorization header
    headers = {
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    req_params = deepcopy(DEFAULT_REQUEST_PARAMS)

    req_params.update(
        params if params is not None else {}
    )


    # Make the request
    response = requests.get(
        get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
        headers=headers,
        params=req_params
    )

    response.raise_for_status()

    return response.json()


def get_request_response_results(endpoint: str, params: Optional[Dict] = None) -> Union[List[Dict], Dict]:
    """
    Run get response against the Metadata endpoint
    :param endpoint:
    :param params:
    :return:
    """
    # Get authorization header
    response_dict = get_request_response(endpoint, params)

    return response_dict['results']


def patch_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Run patch request against the fastq endpoint
    :param endpoint:
    :param params:
    :return:
    """
    # Get authorization header
    headers = {
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    req_params = deepcopy(DEFAULT_REQUEST_PARAMS)

    req_params.update(
        params if params is not None else {}
    )

    # Make the request
    response = requests.patch(
        get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
        headers=headers,
        json=req_params
    )

    response.raise_for_status()

    return response.json()


def post_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Run post request against the fastq endpoint
    :param endpoint:
    :param params:
    :return:
    """
    # Get authorization header
    headers = {
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    req_params = deepcopy(DEFAULT_REQUEST_PARAMS)

    req_params.update(
        params if params is not None else {}
    )

    # Make the request
    response = requests.post(
        get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
        headers=headers,
        json=req_params
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError(f"Error {e} - {response.text}") from e

    return response.json()
