#!/usr/bin/env python3

"""
SFN LAMBDA PLACEHOLDER: __list_fastqs_in_library_as_file_ids_lambda_function_arn__
Intro:

Given a list of json files, convert them into a single csv file and return as a string
"""

# Imports
import typing
from typing import List, Dict, Optional

# Get layer tools
from fastq_tools import (
    get_fastqs_in_library,
    FastqListRow
)

if typing.TYPE_CHECKING:
    from metadata_tools import Library

# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def handler(event, context) -> Dict[str, List[str]]:
    """
    Generate fastqs from library ids as file objects.
    Given a library object as input, convert to fastq objects.
    :param event:
    :param context:
    :return:
    """

    # Get the library object
    library: Library = event.get("libraryObject", None)
    instrument_run_id_list: Optional[List[str]] = event.get("instrumentRunIdList", None)

    # Assert the library object is not None
    assert library is not None, "Library object is None"

    # Get all fastqs for the library
    fastq_objs: List[FastqListRow] = get_fastqs_in_library(
        library['orcabusId'],
    )

    # If instrument runs ids is not None, we will filter the fastqs by the instrument run ids
    if instrument_run_id_list is not None:
        fastq_objs = list(filter(
            lambda fastq_obj: fastq_obj['instrumentRunId'] in instrument_run_id_list,
            fastq_objs
        ))

    return {
        "fastqIdList": list(map(
            lambda fastq_obj_iter_: fastq_obj_iter_['id'],
            fastq_objs
        ))
    }
