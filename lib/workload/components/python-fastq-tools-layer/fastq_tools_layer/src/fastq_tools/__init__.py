#!/usr/bin/env python3

"""
Fastq tools to be used by various lambdas as needed
"""
from .utils.models import(
    FastqListRow,
    FastqStorageObject,
    FileStorageObject,
    FastqSet,
)

from .utils.query_helpers import (
    get_fastq,
    get_fastqs,
    get_fastqs_in_instrument_run_id,
    get_fastqs_in_library,
    get_fastqs_in_library_list,
    get_fastqs_in_libraries_and_instrument_run_id,
    get_fastqs_in_sample,
    get_fastqs_in_subject,
    get_fastqs_in_individual,
    get_fastqs_in_project,
    get_fastq_set
)


from .utils.update_helpers import (
    add_qc_stats,
    add_read_count,
    add_file_compression_information,
    add_ntsm_storage_object,
    add_read_set,
    detach_read_set,
    validate_fastq,
    invalidate_fastq
)

from .utils.workflow_helpers import (
    to_cwl
)


__all__ = [
    # Models
    "FastqListRow",
    "FastqStorageObject",
    "FileStorageObject",
    "FastqSet",

    # Query helpers
    "get_fastq",
    "get_fastqs",
    "get_fastqs_in_instrument_run_id",
    "get_fastqs_in_library",
    "get_fastqs_in_library_list",
    "get_fastqs_in_libraries_and_instrument_run_id",
    "get_fastqs_in_sample",
    "get_fastqs_in_subject",
    "get_fastqs_in_individual",
    "get_fastqs_in_project",

    # Fastq Set Query helpers
    "get_fastq_set",

    # Update helpers
    "add_qc_stats",
    "add_read_count",
    "add_file_compression_information",
    "add_ntsm_storage_object",
    "add_read_set",
    "detach_read_set",
    "validate_fastq",
    "invalidate_fastq",

    # Workflow helpers
    "to_cwl",
]
