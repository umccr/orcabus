#!/usr/bin/env python3

"""
Fastq tools to be used by various lambdas as needed
"""
from .utils.models import(
    FastqListRow,
    FastqListRowCreate,
    FastqStorageObject,
    FileStorageObject,
    FastqSet,
    FastqSetCreate,
    Job,
    JobStatus,
    JobType
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
    get_fastq_set,
    get_fastq_sets,
    get_fastq_jobs
)


from .utils.update_helpers import (
    add_qc_stats,
    add_read_count,
    add_file_compression_information,
    add_ntsm_storage_object,
    add_read_set,
    detach_read_set,
    validate_fastq,
    invalidate_fastq,
    link_fastq_list_row_to_fastq_set,
    unlink_fastq_list_row_from_fastq_set,
    allow_additional_fastqs_to_fastq_set,
    disallow_additional_fastqs_to_fastq_set,
    set_is_current_fastq_set,
    set_is_not_current_fastq_set,
)

from .utils.create_helpers import (
    create_fastq_set_object,
    create_fastq_list_row_object,
)

from .utils.workflow_helpers import (
    to_cwl
)

from .utils.job_helpers import (
    run_qc_stats,
    run_ntsm,
    run_file_compression_stats
)


__all__ = [
    # Models
    "FastqListRow",
    "FastqListRowCreate",
    "FastqStorageObject",
    "FileStorageObject",
    "FastqSet",
    "FastqSetCreate",
    "Job",
    "JobStatus",
    "JobType",

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
    "get_fastq_sets",

    # Job helpers
    "get_fastq_jobs",

    # Create helpers,
    "create_fastq_list_row_object",
    "create_fastq_set_object",

    # Update helpers
    "add_qc_stats",
    "add_read_count",
    "add_file_compression_information",
    "add_ntsm_storage_object",
    "add_read_set",
    "detach_read_set",
    "validate_fastq",
    "invalidate_fastq",
    "link_fastq_list_row_to_fastq_set",
    "unlink_fastq_list_row_from_fastq_set",
    "allow_additional_fastqs_to_fastq_set",
    "disallow_additional_fastqs_to_fastq_set",
    "set_is_current_fastq_set",
    "set_is_not_current_fastq_set",

    # Workflow helpers
    "to_cwl",

    # Job helpers
    "run_qc_stats",
    "run_ntsm",
    "run_file_compression_stats"
]
