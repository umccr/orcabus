#!/usr/bin/env python3

"""
Bunch of useful helper functions for lambdas in the fastq sync service
"""


from os import environ
from typing import Optional, List, Tuple

from fastq_tools import (
    JobStatus, Job, JobType,
    FastqListRow,
    get_fastq_jobs,
    run_qc_stats,
    run_file_compression_stats,
    run_ntsm, FastqSet
)
from fastq_unarchiving_tools import (
    Job as UnarchivingJob,
    JobType as UnarchivingJobType,
    create_job as create_unarchiving_job, get_job_list_for_fastq,
    JobStatus as UnarchivingJobStatus
)
from .globals import (
    ACTIVE_STORAGE_CLASSES, BYOB_BUCKET_PREFIX_ENV_VAR,
    Requirements
)


def has_active_readset(fastq_list_row_obj: 'FastqListRow') -> bool:
    if fastq_list_row_obj['readSet'] is None:
        return False

    readset_objects = list(filter(
        lambda readset_iter_: readset_iter_ is not None,
        [fastq_list_row_obj['readSet']['r1'], fastq_list_row_obj['readSet']['r2']]
    ))

    for readset_object in readset_objects:
        # If the storage class is not in the active storage classes or
        # the s3 uri does not start with the bucket prefix
        # then return False
        if (
                (readset_object['storageClass'] not in ACTIVE_STORAGE_CLASSES)
                or
                (not readset_object['s3Uri'].startswith(environ[BYOB_BUCKET_PREFIX_ENV_VAR]))
        ):
            return False

    return True


def has_qc(fastq_list_row_obj: FastqListRow) -> bool:
    return fastq_list_row_obj['qc'] is not None


def has_fingerprint(fastq_list_row_obj: FastqListRow) -> bool:
    return fastq_list_row_obj['ntsm'] is not None


def has_compression_metadata(fastq_list_row_obj: FastqListRow) -> bool:
    # Check active readset
    if not has_active_readset(fastq_list_row_obj):
        return False

    # Can assert we have an active readset and that the readset is not None

    # Let's check if the compression format is ORA, if not, we can assume that the compression metadata
    # Condition is satisfied
    if fastq_list_row_obj['readSet']['compressionFormat'] != 'ORA':
        return True

    # If the compression format is ORA, then we need to check if the compression metadata is present
    readset_objects = list(filter(
        lambda readset_iter_: readset_iter_ is not None,
        [fastq_list_row_obj['readSet']['r1'], fastq_list_row_obj['readSet']['r2']]
    ))

    for readset_object in readset_objects:
        if readset_object['gzipCompressionSizeInBytes'] is None or readset_object['rawMd5sum'] is None:
            return False

    # If we got to here then the compression metadata is present in all readsets for this fastq list row
    return True


def check_fastq_job(fastq_id: str, job_type: JobType) -> bool:
    """
    Check the fastq doesn't already have jobs running for this particular type
    :param fastq_id:
    :param job_type:
    :return:
    """
    return (
            len(
                list(filter(
                    lambda job_iter_: (
                            (
                                    JobType(job_iter_['jobType']) == job_type
                            ) and
                            (
                                    JobStatus(job_iter_['status']) in [JobStatus.PENDING, JobStatus.RUNNING]
                            )
                    ),
                    get_fastq_jobs(fastq_id)
                ))
            ) == 0
    )


def check_fastq_unarchiving_job(fastq_id: str) -> bool:
    """
    Check that the fastq doesn't already have an unarchiving job running
    Return True if there is no unarchiving jobs running for this fastq list row id
    Return False if there are unarchiving jobs running for this fastq list row id
    :param fastq_id:
    :return:
    """
    return (
            (
                len(get_job_list_for_fastq(fastq_id, UnarchivingJobStatus.PENDING)) == 0
            ) and
            (
                len(get_job_list_for_fastq(fastq_id, UnarchivingJobStatus.RUNNING)) == 0
            )
    )



def run_fastq_job(fastq_list_row: FastqListRow, job_type: JobType) -> Optional[Job]:
    """
    Run a job for a fastq
    :param fastq_id:
    :param job_type:
    :return:
    """
    # Check that the fastq list row has an active read set
    if not has_active_readset(fastq_list_row):
        return None

    # Check if the job is already running
    if not check_fastq_job(fastq_list_row['id'], job_type):
        return None

    # Create the job
    if job_type == JobType.QC:
        return run_qc_stats(fastq_id=fastq_list_row['id'])

    if job_type == JobType.NTSM:
        return run_ntsm(fastq_id=fastq_list_row['id'])

    if job_type == JobType.FILE_COMPRESSION:
        return run_file_compression_stats(fastq_id=fastq_list_row['id'])


def run_fastq_unarchiving_job(fastq_list_row: FastqListRow) -> Optional[UnarchivingJob]:
    create_unarchiving_job(
        fastq_ids=[
            fastq_list_row['id']
        ],
        job_type=UnarchivingJobType.S3_UNARCHIVING
    )


def check_fastq_list_row_against_requirements_list(
        fastq_list_row_obj: FastqListRow,
        requirements: List[Requirements]
) -> Tuple[List[Requirements], List[Requirements]]:
    """
    Given a fastq list row and the requirements, split requirements into two lists, one that is satisfied and one that is not
    """

    satisfied_requirements = []
    unsatisfied_requirements = []

    # Just a large if else block to check the requirements
    for requirement_iter_ in requirements:
        requirement_iter_ = Requirements(requirement_iter_)
        # Check read set
        if requirement_iter_ == Requirements.HAS_ACTIVE_READ_SET:
            if has_active_readset(fastq_list_row_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check qc
        if requirement_iter_ == Requirements.HAS_QC:
            if has_qc(fastq_list_row_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check fingerprint
        if requirement_iter_ == Requirements.HAS_FINGERPRINT:
            if has_fingerprint(fastq_list_row_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check compression metadata
        if requirement_iter_ == Requirements.HAS_FILE_COMPRESSION_INFORMATION:
            if has_compression_metadata(fastq_list_row_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

    return satisfied_requirements, unsatisfied_requirements


def check_fastq_set_against_requirements_bool(
        fastq_set_obj: FastqSet,
        requirements: List[Requirements],
        is_unarchiving_allowed: bool
) -> bool:
    """
    This is used by the lambda that initially checks if all requirements have been met
    We only need a yes or no answer if we're okay to proceed
    :param fastq_set_obj:
    :param requirements:
    :return:
    """
    fastq_list_row_obj: FastqListRow
    for fastq_list_row_obj in fastq_set_obj['fastqSet']:
        if (
                not is_unarchiving_allowed
                and Requirements.HAS_ACTIVE_READ_SET in list(map(lambda x: Requirements(x), requirements))
                and ( not has_active_readset(fastq_list_row_obj) )
                and fastq_list_row_obj['readSet'] is not None
        ):
            raise ValueError("Fastq object is archived but unarchiving is not specified in the fastq sync service")

        s_true, s_false = check_fastq_list_row_against_requirements_list(fastq_list_row_obj, requirements)

        if len(s_false) > 0:
            return False

    return True
