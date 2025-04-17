# Some common routines
import json
from functools import reduce
from operator import concat
from os import environ
from typing import List, Optional, Dict

from dyntastic import A
from fastapi import HTTPException, Query

from ....events.events import put_fastq_set_update_event
from ....models.fastq_list_row import FastqListRowData
from ....models.fastq_set import FastqSetData, FastqSetCreate
from ....models.library import LibraryData

from ....models.job import JobType, JobResponse, JobCreate, JobData

from ....globals import RUN_QC_STATS_AWS_STEP_FUNCTION_ARN_ENV_VAR, \
    RUN_FILE_COMPRESSION_AWS_STEP_FUNCTION_ARN_ENV_VAR, \
    RUN_NTSM_COUNT_AWS_STEP_FUNCTION_ARN_ENV_VAR, RUN_NTSM_EVAL_X_Y_AWS_STEP_FUNCTION_ARN_ENV_VAR, \
    RUN_NTSM_EVAL_X_AWS_STEP_FUNCTION_ARN_ENV_VAR, FastqSetStateChangeStatusEventsEnum

from ....utils import get_sfn_client

from ....models import JobStatus, QueryPagination


def fastq_set_create_obj_to_fastq_set_data_obj(fastq_create_obj: FastqSetCreate) -> FastqSetData:
    """
    Convert a fastq set create object to a fastq set data object
    :param fastq_create_obj:
    :return:
    """
    # Collect each of the fastq_set objects in the fastq_create_obj
    fastq_create_obj_dict = dict(**fastq_create_obj.model_dump(by_alias=True))

    # For each of the fastq_set objects, convert them from string to FastqListRowData objects
    fastq_set_ids: List[str] = list(map(
        lambda fastq_list_row_id_or_obj_iter_: (
            FastqListRowData.get(fastq_list_row_id_or_obj_iter_).id
            if isinstance(fastq_list_row_id_or_obj_iter_, str)
            else fastq_list_row_id_or_obj_iter_
        ),
        fastq_create_obj_dict['fastqSet']
    ))

    # Create the FastqSetData object
    return FastqSetData(
        library=LibraryData(**dict(fastq_create_obj.library)),
        allow_additional_fastq=fastq_create_obj.allow_additional_fastq,
        is_current_fastq_set=fastq_create_obj.is_current_fastq_set,
        fastq_set_ids=fastq_set_ids
    )



# Unlink a fastq set from a file cleanup
def unlink_with_cleanup(fastq_set_obj: FastqSetData, fastq_list_row_obj: FastqListRowData):
    """
    After unlinking a fastq set, we need to do some cleanup.
    This is a common routine since
    * Invalidating a fastq list row (which removes it from a set)
    * Unlink a fastq
    * Delete a fastq (which also removes it from a set)

    This may include -
    * Removing the fastq set from the fastq list row
    * Checking if the fastq set is empty (and deleting it if it is)
    * If the fastq set was the 'current' fastq set, setting the 'current fastq set' to true for another set of the same library
        * Ideally one with the most recent instrument run id

    :param fastq_set_obj:
    :param fastq_list_row_obj:
    :return:
    """
    # Save the fastq list row object (the easy bit)
    fastq_list_row_obj.fastq_set_id = None
    fastq_list_row_obj.save()

    # Remove the fastq list row from the fastq set
    fastq_set_obj.fastq_set_ids = list(filter(
        lambda fastq_list_row_id_iter: fastq_list_row_id_iter != fastq_list_row_obj.id,
        fastq_set_obj.fastq_set_ids
    ))

    # Check if the fastq set is empty
    if len(fastq_set_obj.fastq_set_ids) == 0:
        # Delete the fastq set if it is empty
        fastq_set_obj.delete()

        put_fastq_set_update_event(
            fastq_set_response_object={"fastqSetId": fastq_set_obj.id},
            event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_DELETED
        )

        if not fastq_set_obj.is_current_fastq_set:
            # Nothing else to do here
            return

        # If there are other fastq sets for this library,
        # make the one with the most recent instrument run id
        # The current fastq set
        available_fastq_sets = list(FastqSetData.query(
            A.library_orcabus_id == fastq_list_row_obj.library_orcabus_id,
            index="library_orcabus_id-index",
            load_full_item=True
        ))

        # If there is only one fastq set, make it the current fastq set
        if len(available_fastq_sets) == 1:
            available_fastq_sets[0].is_current_fastq_set = True
            available_fastq_sets[0].save()

            put_fastq_set_update_event(
                fastq_set_response_object=available_fastq_sets[0].to_dict(),
                event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_IS_CURRENT
            )

        # Find all instrument run ids
        elif len(available_fastq_sets) > 1:
            all_instrument_run_ids = list(set(list(reduce(
                concat,
                # Iterate over each of the fastq sets
                list(map(
                    # Iterate over each of the fastq list rows in the fastq set
                    lambda fastq_set_iter_: (
                        # Get the instrument run id for the given fastq list rows
                        list(map(
                            lambda fastq_list_row_iter_: FastqListRowData.get(fastq_list_row_iter_).instrument_run_id,
                            fastq_set_iter_.fastq_set_ids
                        ))
                    ),
                    available_fastq_sets
                ))
            ))))

            # Get the most recent instrument run id
            most_recent_instrument_run_id = max(all_instrument_run_ids)

            # Set the fastq set with the most recent instrument run id as the current fastq set
            for fastq_set_iter in available_fastq_sets:
                instrument_run_id_in_set = list(map(
                    lambda fastq_list_row_iter: FastqListRowData.get(fastq_list_row_iter).instrument_run_id,
                    fastq_set_iter.fastq_set_ids
                ))
                if most_recent_instrument_run_id in instrument_run_id_in_set:
                    fastq_set_iter.is_current_fastq_set = True
                    fastq_set_iter.save()
                    put_fastq_set_update_event(
                        fastq_set_response_object=fastq_set_iter.to_dict(),
                        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_IS_CURRENT
                    )
                    break
    else:
        # Initial save, few cases where we are going to just return
        fastq_set_obj.save()
        put_fastq_set_update_event(
            fastq_set_response_object=fastq_set_obj.to_dict(),
            event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_LIST_ROW_UNLINKED
        )


# Workflow based updates
def run_and_save_fastq_list_row_job(fastq_id: str, job_type: JobType) -> JobResponse:
    fastq = FastqListRowData.get(fastq_id)

    # Check readset is not None
    try:
        assert fastq.read_set is not None, "No FastqPairStorageObject exists for this fastq, cannot run qc stats"
    except AssertionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    existing_jobs = list(
        JobData.query(
            A.fastq_id == fastq.id,
            filter_condition=(
                ( A.job_type == job_type ) &
                ( A.status.is_in([JobStatus.PENDING, JobStatus.RUNNING]))
            ),
            index="fastq_id-index",
            load_full_item=True
        )
    )
    if len(existing_jobs) > 0:
        raise HTTPException(
            status_code=218,
            detail=f"A job already exists for this job in the PENDING or RUNNING state, please wait for it to finish. See '{existing_jobs[0].id}'"
        )

    # Create the job
    job_create = JobCreate(
        fastq_id=fastq.id,
        job_type=job_type
    )

    # Create the job
    job = JobData(**dict(job_create.model_dump(by_alias=True)))

    # Save the job
    job.save()

    if job_type == JobType.QC:
        env_var = RUN_QC_STATS_AWS_STEP_FUNCTION_ARN_ENV_VAR
    elif job_type == JobType.NTSM:
        env_var = RUN_NTSM_COUNT_AWS_STEP_FUNCTION_ARN_ENV_VAR
    elif job_type == JobType.FILE_COMPRESSION:
        env_var = RUN_FILE_COMPRESSION_AWS_STEP_FUNCTION_ARN_ENV_VAR
    else:
        raise HTTPException(status_code=400, detail="Invalid job type")

    # Run qc stats through the AWS step function
    response = get_sfn_client().start_execution(
        stateMachineArn=environ[env_var],
        input=json.dumps(
            {
                "jobId": job.id,
                "fastqId": fastq_id,
            }
        )
    )

    # Add the executionArn to the job
    job.steps_execution_arn = response["executionArn"]
    job.status = JobStatus.RUNNING

    # Save the job
    job.save()

    return job.to_dict()


def run_ntsm_eval(fastq_set_id_x: str, fastq_set_id_y: Optional[str] = None) -> Dict[str, str]:
    if fastq_set_id_y is None:
        env_var = RUN_NTSM_EVAL_X_AWS_STEP_FUNCTION_ARN_ENV_VAR
        input_dict = {
            "fastqSetId": fastq_set_id_x
        }
    else:
        env_var = RUN_NTSM_EVAL_X_Y_AWS_STEP_FUNCTION_ARN_ENV_VAR
        input_dict = {
            "fastqSetIdA": fastq_set_id_x,
            "fastqSetIdB": fastq_set_id_y
        }

    # Run qc stats through the AWS step function
    response = get_sfn_client().start_sync_execution(
        stateMachineArn=environ[env_var],
        input=json.dumps(
            input_dict
        )
    )

    return json.loads(response['output'])


# Define a dependency function that returns the pagination parameters
def get_pagination_params(
    # page must be greater than or equal to 0
    page: int = Query(1, ge=1),
    # rowsPerPage must be greater than 0
    rows_per_page: int = Query(100, gt=1, alias='rowsPerPage')
) -> QueryPagination:
    return {"page": page, "rowsPerPage": rows_per_page}
