#!/usr/bin/env python3

"""
Update fastq object

Given either an ntsm value, file compression information, or qc stats, call the PATCH API endpoint to update the fastq object.

"""

from typing import Dict
from fastq_tools import (
    add_qc_stats,
    add_file_compression_information,
    add_ntsm_storage_object, FastqListRow
)

def handler(event, context) -> Dict[str, FastqListRow]:
    """
    Add fastq object depending on the input parameters.
    :param event:
    :param context:
    :return:
    """
    # Get the fastq id
    fastq_id = event.get("fastqId")

    if event.get("qc") is not None:
        fastq_obj = add_qc_stats(
            fastq_id, event.get("qc")
        )
    elif event.get("fileCompressionInformation") is not None:
        fastq_obj = add_file_compression_information(
            fastq_id, event.get("fileCompressionInformation")
        )
    elif event.get("ntsm") is not None:
        fastq_obj = add_ntsm_storage_object(
            fastq_id, event.get("ntsm")
        )
    else:
        raise ValueError("No valid parameters provided")

    return {
        "fastqObj": fastq_obj
    }
