#!/usr/bin/env python3
from typing import Dict, Optional, List, Union
from urllib.parse import urlunparse, urlparse, unquote

# Standard imports
import requests
import logging
from copy import deepcopy

# Locals
from .globals import (
    FILE_SUBDOMAIN_NAME,
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


def get_url(endpoint: str) -> str:
    """
    Get the URL for the filemanager endpoint
    :param endpoint:
    :return:
    """
    # Get the hostname
    hostname = get_hostname()

    return str(urlunparse(
        (
            "https",
            ".".join([FILE_SUBDOMAIN_NAME, hostname]),
            endpoint,
            None, None, None
        )
    ))

def strip_query(url: str) -> str:
    url_obj = urlparse(url)

    return str(urlunparse(
        (
            url_obj.scheme,
            url_obj.netloc,
            url_obj.path,
            None, None, None
        )
    ))


def get_response(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Run get response against the filemanager endpoint
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

    return response_json



def get_request_response_results(endpoint: str, params: Optional[Dict] = None) -> Union[List[Dict], List[str]]:
    """
    Run get response against the filemanager endpoint
    :param endpoint:
    :param params:
    :return:
    """
    # Get authorization header
    headers = {
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    req_params = deepcopy(DEFAULT_REQUEST_PARAMS)

    # Add endpoint params
    if urlparse(endpoint).query is not None and not urlparse(endpoint).query == "":
        req_params.update(
            dict(map(
                lambda x: (x.split("=")[0], x.split("=")[1]),
                urlparse(endpoint).query.split("&")
            ))
        )

    req_params.update(
        params if params is not None else {}
    )

    # Make the request
    response = requests.get(
        get_url(endpoint) if not urlparse(endpoint).scheme else strip_query(endpoint),
        headers=headers,
        params=req_params
    )

    response.raise_for_status()

    response_json = response.json()

    if 'links' not in response_json.keys():
        return [response_json]

    if 'next' in response_json['links'].keys() and response_json['links']['next'] is not None:
        return response_json['results'] + get_request_response_results(unquote(response_json['links']['next']))
    return response_json['results']


def patch_response(endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
    """
    Run patch response against the filemanager endpoint
    :param endpoint:
    :param params:
    :param json_data:
    :return:
    """
    # Get authorization header
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    # Make the request
    response = requests.patch(
        get_url(endpoint) if not urlparse(endpoint).scheme else endpoint,
        headers=headers,
        params=params,
        json=json_data
    )

    response.raise_for_status()

    response_json = response.json()

    return response_json