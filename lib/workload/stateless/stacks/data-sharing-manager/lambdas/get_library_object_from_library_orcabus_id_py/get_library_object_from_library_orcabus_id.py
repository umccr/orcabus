#!/usr/bin/env python3

"""
LAMBDA_ARN_SFN_PLACEHOLDER: __get_library_object_from_library_orcabus_id_lambda_function_arn__


Get Library Object from Library ID
"""

# Imports
from typing import Dict
from metadata_tools import (
    Library, get_library_from_library_orcabus_id
)

# Extend class by LibraryExt to contain Instrument Run ID

# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context) -> Dict[str, Library]:
    """
    Given a library id, return the library object
    :param event:
    :param context:
    :return:
    """
    # Get the library id from the event input
    library_orcabus_id = event.get("libraryOrcabusId")

    # Assert that the library is not None:
    assert library_orcabus_id is not None, "Library ID is None"

    # Get the library object from the library id
    library: Library = get_library_from_library_orcabus_id(library_orcabus_id)

    # Assert that the library is not None:
    assert library is not None, f"Library is None, could not find library with orcabus id: {library_orcabus_id}"

    # Return the library object
    return {
        "library": library
    }
