#!/usr/bin/env python
from typing import Union, Dict, List

from .globals import LIBRARY_ENDPOINT
from .requests_helpers import get_request_response_results


def get_library_from_library_id(library_id: Union[int | str]) -> Dict:
    """
    Get library from the library id
    :param library_id:
    :return:
    """
    # Get library id
    # We have an internal id, convert to int
    params = {
        "library_id": library_id
    }

    # Get library
    return get_request_response_results(LIBRARY_ENDPOINT, params)[0]


def get_library_from_library_orcabus_id(library_orcabus_id: Union[int | str]) -> Dict:
    """
    Get library from the library id
    :param library_orcabus_id:
    :return:
    """
    # Get library id
    # We have an internal id, convert to int
    params = {
        "orcabus_id": library_orcabus_id
    }

    # Get library
    return get_request_response_results(LIBRARY_ENDPOINT, params)[0]



def get_subject_from_library_id(library_id: Union[int | str]) -> Dict:
    """
    Given a library id, collect the subject id
    :param library_id:
    :return:
    """
    from .subject_helpers import get_subject_from_subject_id

    # Get the subject linked to this library id
    subject_id = get_library_from_library_id(library_id)["subject"]['subjectId']

    return get_subject_from_subject_id(subject_id)


def get_library_type(library_id: Union[int | str]) -> Union[str | None]:
    """
    Given a library id, collect the library id type
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("type")


def get_library_assay_type(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library assay type
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("assay")


def get_library_phenotype(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library phenotype
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("phenotype")


def get_library_workflow(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library workflow
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("workflow")


def get_library_project_owner(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library project owner
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("projectOwner")


def get_library_project_name(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library workflow
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("projectName")


def get_all_libraries() -> List[Dict]:
    """
    Collect all libraries from the database
    :return:
    """
    return get_request_response_results(LIBRARY_ENDPOINT)
