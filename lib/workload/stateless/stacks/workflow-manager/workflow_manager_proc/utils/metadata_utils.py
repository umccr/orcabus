import re
import logging
from itertools import batched
from typing import Dict, List

from .request_utils import get_request_response_results

logger = logging.getLogger(__name__)

regex_ulid = r"[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}"

lib_orca_id_regex = re.compile(r"(lib\.)?" + regex_ulid)
lib_lab_id_regex = re.compile(r"L(PRJ)?\d{6,7}")

metadata_domain = 'metadata.dev.umccr.org'  # FIXME: get from env var
api_root = 'api/v1/'


def get_libraries(library_ids: List[str]) -> List[dict]:
    """
    Get library records from the metadata service given a list of library IDs.
    Note: The ID of the library is either the "lab" ID, e.g. L2401464
          or the OrcaBus internal ID, e.g. 01J8ES926Z4XZVYFE3MZECGXK9 or lib.01J8ES926Z4XZVYFE3MZECGXK9

    :param: list of library IDs
    :return: the list of metadata record for the libraries.
    """
    endpoint = api_root + "library"

    library_records = []  # collect the total list of results
    n_batches = 0  # record the number of batches for potential post query clean-up
    for batch in batched(library_ids, 20):
        n_batches += 1
        print(batch)
        params = {
            "libraryId": [],
            "orcabusId": []
        }
        for id in batch:
            print(id)
            if lib_lab_id_regex.fullmatch(id):
                params["libraryId"].append(id)
            elif lib_orca_id_regex.fullmatch(id):
                params["orcabusId"].append(id)
            else:
                logger.warning(f"Ignoring {id}. Not a valid library ID!")

        print(f"querying with {params}")
        result = get_request_response_results(metadata_domain, endpoint, params)
        library_records.extend(result)

    # post query clean-up: deal with possible duplicate results
    # NOTE: the Metadata Manager API already deduplicates for results returned for a single query,
    #       but due to the batching we may run multiple queries that can query with the same IDs
    if n_batches > 1:
        library_records = remove_duplicate_orcabus_records(library_records)

    return library_records


def remove_duplicate_orcabus_records(records):
    """
    Remove duplicates from a list of OrcaBus records.
    A OrcaBus record is defined as a dict that contains a 'orcabusId' key at the top level.
    Deduplication is performed by removing dicts that have the same 'orcabusId'.
    """
    print('removing duplicates')
    result = []
    orcabus_ids = set()
    for record in records:
        orcabus_id = record['orcabusId']
        if orcabus_id not in orcabus_ids:
            orcabus_ids.add(orcabus_id)
            result.append(record)

    return result