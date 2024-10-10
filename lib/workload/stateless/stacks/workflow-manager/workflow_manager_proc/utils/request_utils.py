import requests
import logging
from copy import deepcopy
from typing import Dict, Optional, List
from urllib.parse import urlunparse, urlparse

from .aws_utils import get_orcabus_token

DEFAULT_REQUEST_PARAMS = {
    "rowsPerPage": 1000
}

# Set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_api_url(domain: str, endpoint: str) -> str:
    """
    Get the URL for an OrcaBus endpoint
    :param domain: the domain of the API (e.g. metadata.dev.umccr.org)
    :param endpoint: the endpoint of the API (e.g. api/v1/library)
    """
    return urlunparse(("https", domain, endpoint, None, None, None))


def get_request_response_results(domain: str, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
    """
    Run get response against an OrcaBus endpoint
    :param domain: the domain of the API (e.g. metadata.dev.umccr.org)
    :param endpoint: the endpoint of the API (e.g. api/v1/library)
    :param params: optional query parameters
    :return:
    """
    # Get authorization header
    headers = {
        "Authorization": f"Bearer {get_orcabus_token()}"
    }

    req_params = deepcopy(DEFAULT_REQUEST_PARAMS)
    if params:
        req_params.update(params)

    # Make the request
    response = requests.get(
        get_api_url(domain, endpoint) if not urlparse(endpoint).scheme else endpoint,
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