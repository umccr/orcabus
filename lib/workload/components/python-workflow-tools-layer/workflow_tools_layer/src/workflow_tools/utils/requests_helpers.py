#!/usr/bin/env python3
from typing import Dict, Optional, List, Union
from urllib.parse import urlunparse, urlparse

# Standard imports
import requests
import logging
from copy import deepcopy

from . import strip_context_from_orcabus_id
# Locals
from .globals import (
    WORKFLOW_SUBDOMAIN_NAME,
)

from .aws_helpers import (
    get_orcabus_token, get_hostname
)

# Globals
DEFAULT_REQUEST_PARAMS = {
    "rowsPerPage": 1000
}

# Set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def url_path_ext(url: str, path: str) -> str:
    """
    Append a path to a URL
    :param url:
    :param path:
    :return:
    """
    return str(urlunparse(
        urlparse(url)._replace(path=f"{urlparse(url).path}/{path}")
    ))


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
            ".".join([WORKFLOW_SUBDOMAIN_NAME, hostname]),
            endpoint,
            None, None, None
        ]
    )


def get_request_results(endpoint: str, orcabus_id: str) -> Union[List, Dict]:
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

    # Make the request
    response = requests.get(
        url_path_ext(
            get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
            strip_context_from_orcabus_id(orcabus_id)
        ),
        headers=headers,
    )

    response.raise_for_status()

    return response.json()


def get_request_results_ext(endpoint: str, orcabus_id: str, url_extension: str) -> Union[List, Dict]:
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

    # Make the request
    response = requests.get(
        url_path_ext(
            get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
            strip_context_from_orcabus_id(orcabus_id) + "/" + url_extension
        ),
        headers=headers,
        params=req_params
    )

    response.raise_for_status()

    return response.json()


def get_request_response_results(endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
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

    response_json = response.json()

    if 'links' not in response_json.keys():
        return [response_json]

    if 'next' in response_json['links'].keys() and response_json['links']['next'] is not None:
        return response_json['results'] + get_request_response_results(response_json['links']['next'])
    return response_json['results']
