#!/usr/bin/env python3

"""
SFN LAMBDA PLACEHOLDER: __list_fastqs_in_library_as_file_ids_lambda_function_arn__
Intro:

Given a list of json files, convert them into a single csv file and return as a string
"""

# Imports
import typing
from typing import List, Dict, Optional
from functools import reduce
from operator import concat

# Get layer tools
from fastq_tools import (
    get_fastqs_in_library,
    FastqListRow
)
from filemanager_tools import (
    get_file_object_from_ingest_id,
    FileObject
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
    For each fastq object for the library, collect the file objects and then write out as ingest_ids
    :param event:
    :param context:
    :return:
    """

    # Get the library object
    library: Library = event.get("libraryObject", None)
    instrument_run_id_list: Optional[List[str]] = event.get("instrumentRunIds", None)

    # Assert the library object is not None
    assert library is not None, "Library object is None"

    # Get all fastqs for the library
    fastq_objs: List[FastqListRow] = get_fastqs_in_library(
        library,
    )

    # If instrument runs ids is not None, we will filter the fastqs by the instrument run ids
    if instrument_run_id_list is not None:
        fastq_objs = list(filter(
            lambda fastq_obj: fastq_obj['instrumentRunId'] in instrument_run_id_list,
            fastq_objs
        ))

    # Get the s3 ingest ids
    s3_ingest_ids = list(reduce(
        # Flatten the list of [ [r1, r2], [r1, r2], ...] into a single list of [r1, r2, r1, r2, ...]
        concat,
        # For each fastq object, get the ingest ids for r1 and r2
        list(map(
            # Filter out r2 if it doesn't exist
            lambda fastq_obj_iter_ : list(filter(
                lambda ingest_id_iter_: ingest_id_iter_ is not None,
                # Get the s3IngestId from the fastq objects
                [
                    get_file_object_from_ingest_id(fastq_obj_iter_['readSet']['r1']['s3IngestId']),
                    (
                        get_file_object_from_ingest_id(fastq_obj_iter_['readSet']['r2']['s3IngestId'])
                        if fastq_obj_iter_['readSet']['r2'] else None
                    ),
                ],
            )),
            fastq_objs
        ))
    ))

    # Get the file objects from the s3 ingest ids
    file_objs: List[FileObject] = list(map(
        lambda ingest_id: get_file_object_from_ingest_id(ingest_id),
        s3_ingest_ids
    ))

    return {
        "s3ObjectIdList": list(map(
            lambda file_obj_iter_: file_obj_iter_['s3ObjectId'],
            file_objs
        ))
    }