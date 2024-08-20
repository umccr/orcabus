#!/usr/bin/env python
from typing import Union, Dict, List

from .requests_helpers import get_request_response_results


def get_library_from_library_id(library_id: Union[int | str]) -> Dict:
    """
    Get library from the library id
    :param library_id:
    :return:
    """
    endpoint = "api/v1/library"

    # Get library id
    if isinstance(library_id, str):
        # We have an internal id, convert to int
        params = {
            "library_id": library_id
        }
    else:
        endpoint = f"{endpoint}/{library_id}"
        params = {}

    # Get library
    return get_request_response_results(endpoint, params)[0]


def get_subject_from_library_id(library_id: Union[int | str]) -> Dict:
    """
    Given a library id, collect the subject id
    :param library_id:
    :return:
    """
    from .specimen_helpers import get_specimen_from_specimen_id
    from .subject_helpers import get_subject_from_subject_id

    # Get the specimen linked to this library id
    specimen_id = get_library_from_library_id(library_id)["specimen"]

    specimen_obj = get_specimen_from_specimen_id(specimen_id)

    if "subjects" in specimen_obj.keys() and len(specimen_obj["subjects"]) > 0:
        subject_id = specimen_obj["subjects"][0]
    elif "subject" in specimen_obj.keys():
        subject_id = specimen_obj["subject"]
    else:
        raise KeyError(f"Subject not found for library id: {library_id}")

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

    return library.get("project_owner")


def get_library_project_name(library_id: str) -> Union[str | None]:
    """
    Given a library id, collect the library workflow
    :param library_id:
    :return:
    """
    library = get_library_from_library_id(library_id)

    return library.get("project_name")


def get_all_libraries() -> List[Dict]:
    """
    Collect all libraries from the database
    :return:
    """
    endpoint = "api/v1/library"

    return get_request_response_results(endpoint)
