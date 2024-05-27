#!/usr/bin/env python3

"""
Custom script for each library id, generate a samplesheet and fastq list row set

"""

from typing import List


def get_fastq_list_rows_for_library_id(library_id: str, fastq_list_rows: List):
    return list(
        filter(
            lambda fastq_list_row_iter: fastq_list_row_iter.get("RGSM") == library_id,
            fastq_list_rows
        )
    )


def handler(event, context):
    """
    Take in the fastq list rows, and samplesheet
    :param event:
    :param context:
    :return:
    """
    # Get the library id
    library_id = event.get("library_id")
    fastq_list_rows = event.get("fastq_list_rows")

    return {
        "fastq_list_rows": get_fastq_list_rows_for_library_id(library_id, fastq_list_rows),
    }
