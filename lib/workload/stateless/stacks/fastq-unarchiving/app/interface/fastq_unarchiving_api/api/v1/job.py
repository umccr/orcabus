#!/usr/bin/env python3

"""

Routes for the API V1 Fastq endpoint

This is the list of routes available
-

"""

# Standard imports
from datetime import datetime, timezone
from os import environ
from textwrap import dedent
from typing import Annotated

from fastapi import Depends, Query, Body
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist


# Model imports
from ...models.job import JobData, JobQueryPaginatedResponse, JobCreate, JobResponse, JobPatch
from ...models.query import JobQueryParameters
from ...models import QueryPagination, JobStatus
from ...globals import UNARCHIVING_JOB_STATE_MACHINE_ARN_ENV_VAR, get_default_job_patch_entry
from ...utils import sanitise_ufr_orcabus_id, launch_sfn, abort_sfn
from ...events import put_job_create_event, put_job_update_event

router = APIRouter()


# Define a dependency function that returns the pagination parameters
def get_pagination_params(
    # page must be greater than or equal to 1
    page: int = Query(1, gt=0),
    # rowsPerPage must be greater than 0
    rows_per_page: int = Query(100, gt=0, alias='rowsPerPage')
) -> QueryPagination:
    return {"page": page, "rowsPerPage": rows_per_page}


## Query options
# - Get /jobs endpoint for a given fastq list row id
@router.get(
    "/",
    tags=["query"]
)
async def get_jobs(
        job_query_parameters: JobQueryParameters = Depends(),
        # Pagination options
        pagination: QueryPagination = Depends(get_pagination_params),
) -> JobQueryPaginatedResponse:
    # Job Query Parameters include start time, end time and status
    # We also include the fastq id as a parameter however this is not indexed and so needs to be filtered manually
    # As such we will first filter by the indexed parameters and then filter by the fastq id
    # If no indexed parameters are provided, we will perform a scan and then filter by the fastq id

    # Let's try and generate the filter expression
    # We have the following indexed keys in the database (tied to status),
    filter_expression = None
    if job_query_parameters.created_before is not None:
        filter_expression = filter_expression & (A.start_time <= job_query_parameters.created_before)
    if job_query_parameters.created_after is not None:
        filter_expression = filter_expression & (A.start_time >= job_query_parameters.created_after)
    if job_query_parameters.completed_before is not None:
        filter_expression = filter_expression & (A.end_time <= job_query_parameters.completed_before)
    if job_query_parameters.completed_after is not None:
        filter_expression = filter_expression & (A.end_time >= job_query_parameters.completed_after)

    # To query or to scan, depends on if the status is provided
    # Since the status is indexed to the jobs
    if job_query_parameters.status_list is not None:
        # - start_time
        # - end_time
        # With the following query parameters
        # - created_before
        # - created_after
        # - completed_before
        # - completed_after
        job_list = []
        for status_iter in job_query_parameters.status_list:
            job_list += list(JobData.query(
                A.status == status_iter,
                filter_condition=filter_expression,
                index="status-index",
                load_full_item=True
            ))
    else:
        job_list = list(JobData.scan(
            filter_condition=filter_expression,
            load_full_item=True
        ))

    # Now check if the fastq_id_list is in the query parameters
    if job_query_parameters.fastq_id_list is not None:
        job_list = list(filter(
            lambda job_iter_: len(set(job_query_parameters.fastq_id_list).intersection(set(job_iter_.fastq_ids))) > 0,
            job_list
        ))

    return JobQueryPaginatedResponse.from_results_list(
        results=list(map(
            lambda job_iter_: job_iter_.to_dict(),
            job_list,
        )),
        query_pagination=pagination,
        params_response=dict(filter(
            lambda kv: kv[1] is not None,
            dict(
                **job_query_parameters.to_params_dict(),
                **pagination
            ).items()
        )),
    )


# Get a job from orcabus id
@router.get(
    "/{job_id}",
    tags=["query"],
    description="Get a job object"
)
async def get_jobs(job_id: str = Depends(sanitise_ufr_orcabus_id)) -> JobResponse:
    try:
        return JobData.get(job_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# Create a job object
@router.post(
    "/",
    tags=["job create"],
    description=dedent("""
    Create a new fastq unarchiving job.
    Given a list of fastq list row orcabus ids, create a new unarchiving job. 
    This will create a new job object and return the job object as a response.
    """)
)
async def create_job(job_obj: JobCreate) -> JobResponse:
    # First convert the CreateFastqListRow to a FastqListRow
    job_obj = JobData(**dict(job_obj.model_dump(by_alias=True)))

    # Query any PENDING / RUNNING jobs that may contain the same fastq id?
    job_list = []
    for status_iter_ in ["PENDING", "RUNNING"]:
        job_list += list((
            JobData.query(
                A.status == status_iter_,
                index="status-index",
                load_full_item=True
            )
        ))

    try:
        for job in job_list:
            if len(set(job.fastq_ids).intersection(set(job_obj.fastq_ids))) > 0:
                raise AssertionError(f"Job with fastq id '{job_obj.fastq_ids}' already exists")
    except AssertionError as e:
        # Return a 409 Conflict if the fastq already exists
        raise HTTPException(status_code=409, detail=str(e))

    # Launch the job
    job_obj.status = JobStatus.PENDING
    job_obj.start_time = datetime.now(timezone.utc)
    job_obj.steps_execution_arn = launch_sfn(
        sfn_name=environ[UNARCHIVING_JOB_STATE_MACHINE_ARN_ENV_VAR],
        sfn_input={
            "jobId": job_obj.id,
            "fastqIdList": job_obj.fastq_ids,
        }
    )

    # Save the job object
    # Save the fastq
    job_obj.save()

    # Create the dictionary
    job_dict = job_obj.to_dict()

    # Generate a create event
    put_job_create_event(job_dict)

    # Return the fastq as a dictionary
    return job_dict


@router.patch(
    "/{job_id}",
    tags=["job update"],
    description=dedent("""
    Update a job status. This will update a job and set the status to the new status.
    This is internal use only and should only be used by the job execution step function.
    """)
)
async def update_job(job_id: str = Depends(sanitise_ufr_orcabus_id), job_status_obj: Annotated[JobPatch, Body()] = get_default_job_patch_entry()) -> JobResponse:
    if job_status_obj.status not in [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.SUCCEEDED]:
        raise HTTPException(status_code=400, detail="Invalid status provided, must be one of RUNNING, FAILED or SUCCEEDED")
    try:
        job_obj = JobData.get(job_id)
        job_obj.status = job_status_obj.status
        # Add in end time if the job is in a terminal state
        if job_obj.status in [JobStatus.SUCCEEDED, JobStatus.FAILED]:
            job_obj.end_time = datetime.now(timezone.utc)
        job_obj.save()
        job_dict = job_obj.to_dict()
        put_job_update_event(job_dict)
        return job_dict
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{job_id}:abort",
    tags=["job abort"],
    description=dedent("""
    Abort a job. This will abort a job and set the status to ABORTED
    """)
)
async def abort_job(job_id: str = Depends(sanitise_ufr_orcabus_id)) -> JobResponse:
    try:
        job_obj = JobData.get(job_id)

        if not job_obj.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise AssertionError("Job is not in a state that can be aborted")

        job_obj.status = JobStatus.ABORTED

        # Abort the execution arn
        abort_sfn(job_obj.steps_execution_arn)

        job_obj.save()
        return job_obj.to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{job_id}",
    tags=["job delete"],
    description=dedent("""
    Delete a job. This will delete a job object. 
    """)
)
async def delete_job(job_id: str = Depends(sanitise_ufr_orcabus_id)) -> JobResponse:
    try:
        job_obj = JobData.get(job_id)
        if job_obj.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise AssertionError("Job is in a state that cannot be deleted")
        job_obj.delete()
        return job_obj.to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))