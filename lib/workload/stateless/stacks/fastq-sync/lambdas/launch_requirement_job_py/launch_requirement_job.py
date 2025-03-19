#!/usr/bin/env python3

"""
Given a requirement item and a fastq list row id, launch a job against the requirement item

For qc, fingerprint or compression, we use the fastq api endpoint,
For unarchiving we use the fastq unarchiving endpoint

The requirementType input will be one of the following:

ACTIVE_READSET
QC
FINGERPRINT
COMPRESSION_METADATA

"""

from fastq_tools import (
    get_fastq, JobType,
)

from fastq_sync_tools import (
    Requirements,
    run_fastq_job,
    run_fastq_unarchiving_job,
    check_fastq_unarchiving_job,
    check_fastq_job
)


def handler(event, context):
    """
    Get the requirement type and launch the job
    :param event:
    :param context:
    :return:
    """
    # Get inputs
    fastq_list_row_id = event['fastqListRowId']
    requirement_type = Requirements[event['requirementType']]

    # Get the fastq list row as an object
    fastq_list_row_obj = get_fastq(fastq_list_row_id, includeS3Details=True)

    # Launch unarchiving job
    if check_fastq_unarchiving_job(fastq_list_row_id) and requirement_type == Requirements.HAS_ACTIVE_READ_SET:
        run_fastq_unarchiving_job(
            fastq_list_row_obj
        )

    # Run internal jobs
    if check_fastq_job(fastq_list_row_id, JobType.QC) and requirement_type == Requirements.HAS_QC:
        run_fastq_job(fastq_list_row_id, JobType.QC)

    if check_fastq_job(fastq_list_row_id, JobType.NTSM) and requirement_type == Requirements.HAS_FINGERPRINT:
        run_fastq_job(fastq_list_row_id, JobType.NTSM)

    if check_fastq_job(fastq_list_row_id, JobType.FILE_COMPRESSION) and requirement_type == Requirements.HAS_FILE_COMPRESSION_INFORMATION:
        run_fastq_job(fastq_list_row_id, JobType.FILE_COMPRESSION)
