#!/usr/bin/env python3

"""
Update helpers for the update script.

- add_qc_stats
- add_read_count
- add_ntsm_storage_object / add_ntsm
- add_fastq_pair_storage_object / add_read_set
- detach_fastq_pair_storage_object / detach_read_set
- validate
- invalidate
"""

# Standard imports

# Local imports
from .globals import FASTQ_LIST_ROW_ENDPOINT
from .request_helpers import patch_request
from .models import QcStats, FastqListRow, ReadCount, FileCompressionInformation, FileStorageObject, ReadSet


def add_qc_stats(fastq_id: str, qc_stats: QcStats) -> FastqListRow:
    """
    Add QC stats to a fastq_id.

    :param fastq_id: Fastq str
    :param qc_stats: Dictionary of QC stats
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/addQcStats",
        params=qc_stats
    )


def add_read_count(fastq_id: str, read_count: ReadCount) -> FastqListRow:
    """
    Add read count to a fastq id
    :param fastq_id:
    :param read_count:
    :return:
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/addReadCount",
        params=read_count
    )


def add_file_compression_information(fastq_id: str, file_compression_information: FileCompressionInformation) -> FastqListRow:
    """
    Add file compression information to a fastq id
    :param fastq_id:
    :param file_compression_information:
    :return:
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/addFileCompressionInformation",
        params=file_compression_information
    )


def add_ntsm_storage_object(fastq_id: str, ntsmFastqStorageObject: FileStorageObject) -> FastqListRow:
    """
    Add a Ntsm storage object to a fastq id.

    :param fastq_id: Fastq str
    :param ntsm_id: Ntsm str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/addNtsmStorageObject",
        params=ntsmFastqStorageObject
    )


def add_read_set(fastq_id: str, read_set: ReadSet) -> FastqListRow:
    """
    Add a read set to a fastq id.

    :param fastq_id: Fastq str
    :param read_set: ReadSet str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/addFastqPairStorageObject",
        params=read_set
    )

def detach_read_set(fastq_id: str, read_set: ReadSet) -> FastqListRow:
    """
    Detach a read set to a fastq id.

    :param fastq_id: Fastq str
    :param read_set: ReadSet str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/detachFastqPairStorageObject",
        params=read_set
    )


def validate_fastq(fastq_id: str) -> FastqListRow:
    """
    Validate a fastq id.

    :param fastq_id: Fastq str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/validate"
    )


def invalidate_fastq(fastq_id: str) -> FastqListRow:
    """
    Invalidate a fastq id.

    :param fastq_id: Fastq str
    """
    return patch_request(
        f"{FASTQ_LIST_ROW_ENDPOINT}/{fastq_id}/invalidate"
    )
