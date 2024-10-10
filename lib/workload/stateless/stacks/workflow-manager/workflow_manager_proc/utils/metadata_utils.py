#!/usr/bin/env python
import re
from itertools import batched
from typing import Dict, List


from .request_utils import get_request_response_results

regex_ulid = r"[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}"

lib_orca_id_regex = re.compile(r"(lib\.)?" + regex_ulid)
lib_lab_id_regex = re.compile(r"L\d{7}")

metadata_domain = 'metadata.dev.umccr.org'  # FIXME: get from env var
api_root = 'api/v1/'


def get_library_from_library_id(library_id: str) -> Dict:
    """
    Get library record from the metadata service given its ID.
    Note: The ID of the library is either the "lab" ID, e.g. L1900368
          or the OrcaBus internal ID, e.g. 01G9HHNTQY2E8HM5N9AE5SQBXQ or lib.01G9HHNTQY2E8HM5N9AE5SQBXQ

    :param: the library ID
    :return: the metadata record for the library, if found. None otherwise.
    """
    if lib_lab_id_regex.fullmatch(library_id):
        # lab library ID format, we need to query with the 'library_id' parameter.
        endpoint = api_root + "library"
        params = {
            "library_id": library_id
        }
    elif lib_orca_id_regex.fullmatch(library_id):
        # OrcaBus ID format, can retrieve from its endpoint. No need for parameters.
        endpoint = api_root + "library/" + library_id
        params = {}
    else:
        raise ValueError(f"Not a valid library ID: {library_id}")

    result = get_request_response_results(metadata_domain, endpoint, params)
    # we only expect a single record in response
    return result[0]


def get_library_from_library_id(library_ids: List[str]) -> List[dict]:
    """
    Get library records from the metadata service given a list of library IDs.
    Note: The ID of the library is either the "lab" ID, e.g. L1900368
          or the OrcaBus internal ID, e.g. 01G9HHNTQY2E8HM5N9AE5SQBXQ or lib.01G9HHNTQY2E8HM5N9AE5SQBXQ

    :param: list of library IDs
    :return: the list of metadata record for the libraries.
    """
    for batch in batched(library_ids, 10):
        for id in batch:
            



    pass
