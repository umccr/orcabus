#!/usr/bin/env python3

"""
LAMBDA_ARN_SFN_PLACEHOLDER: __get_lims_from_library_lambda_function_arn__


Given a library object, return a row from the LIMS database that corresponds to the library.
"""

# Imports
from typing import Optional, List, Dict

# Layer tools
from metadata_tools import (
    generate_lims_row, LimsRow, Library
)
from fastq_tools import get_fastqs_in_library, FastqListRow

# Set logging
import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def get_instrument_runs_for_library_object(library: Library) -> List[str]:
    # FIXME - use the sequence run manager in the future, but for now use the fastq manager
    # FIXME - to determine the instrument run ids that this library belongs to
    # Get instrument run ids in library
    # Get all fastqs for the library
    fastq_objs: List[FastqListRow] = get_fastqs_in_library(
        library['orcabusId'],
    )
    # Get instrument run ids
    return list(set(list(map(
        lambda fastq_obj_iter: fastq_obj_iter.get("instrumentRunId"),
        fastq_objs
    ))))


def handler(event, context) -> Dict[str, List[LimsRow]]:
    """
    Given a library object, return the lims row
    :param event:
    :param context:
    :return:
    """
    # Get the library object
    library: Library = event.get("libraryObject", None)
    instrument_run_ids_for_library = get_instrument_runs_for_library_object(library)

    # Optional input is the instrument run id list
    instrument_run_id_list: Optional[List[str]] = event.get("instrumentRunIds", None)

    # Filter out instrument_run_ids_for_library by those in the instrument_run_id_list
    instrument_run_id_list = list(filter(
        lambda instrument_run_id_iter_: instrument_run_id_iter_ in instrument_run_id_list,
        instrument_run_ids_for_library
    ))

    # Generate lims row
    lims_rows = list(map(
        lambda instrument_run_id_iter_:
            generate_lims_row(
                library_id=library['libraryId'],
                instrument_run_id=instrument_run_id_iter_
            ),
        instrument_run_id_list
    ))

    # Return lims rows
    return {
        "limsRows": lims_rows
    }


