#!/usr/bin/env python3

"""
So you've sent your data

A Get request can be made using the push job id to get the status of the push job.
api/v1/push/{push_job_id}.

The push job object contains the following fields:
  * id
  * packageId
  * status
  * startTime
  * endTime

Status's include:
* PENDING
* RUNNING
* FAILED
* SUCCEEDED

An event is raised every time a status job changes.

We can also view the list of valid destination URI prefixes for the push job with the following get endpoint
push/ListValidDestinationPrefixes

We can query by status or package name or package id.

We can also 'patch' a push job to update the status of the push job.
This is used internally by the step function to update the status of the push job, which in turn generates an event.

"""


# Standard imports
from textwrap import dedent
from typing import Annotated

from fastapi import Depends, Query, Body
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist
from datetime import datetime, timezone

# Model imports
from ...models.push import (
    PushJobData, PushJobQueryPaginatedResponse, \
    PushJobResponse
)

from ...models import QueryPagination, JobStatus, JobPatch
from ...globals import get_default_job_patch_entry
from ...utils import abort_sfn, sanitise_psh_orcabus_id
from ...events.push import put_push_job_update_event
from ...models.query import PushQueryParameters

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
    "",
    tags=["push job query"]
)
async def get_push_jobs(
        push_query_parameters: PushQueryParameters = Depends(),
        # Pagination options
        pagination: QueryPagination = Depends(get_pagination_params),
) -> PushJobQueryPaginatedResponse:
    # Package Query Parameters include start time, end time and status
    # We allow for queries by package name and status.

    # Let's try and generate the filter expression
    # We have the following indexed keys in the database (tied to status),
    filter_expression = None
    if push_query_parameters.created_before is not None:
        filter_expression = filter_expression & (A.start_time <= push_query_parameters.created_before)
    if push_query_parameters.created_after is not None:
        filter_expression = filter_expression & (A.start_time >= push_query_parameters.created_after)
    if push_query_parameters.completed_before is not None:
        filter_expression = filter_expression & (A.end_time <= push_query_parameters.completed_before)
    if push_query_parameters.completed_after is not None:
        filter_expression = filter_expression & (A.end_time >= push_query_parameters.completed_after)

    # To query or to scan, depends on if the status is provided
    # Since the status is indexed to the jobs
    # FIXME - could in theory be adding status to the filter expression too
    if push_query_parameters.package_id_list is not None:
        job_list = []
        for package_id_iter in push_query_parameters.package_id_list:
            job_list += list(PushJobData.query(
                A.package_id == package_id_iter,
                filter_condition=filter_expression,
                index="package_id-index",
                load_full_item=True
            ))
    elif push_query_parameters.package_name_list is not None:
        job_list = []
        for package_name_iter in push_query_parameters.package_name_list:
            job_list += list(PushJobData.query(
                A.package_name == package_name_iter,
                filter_condition=filter_expression,
                index="package_name-index",
                load_full_item=True
            ))
    elif push_query_parameters.status_list is not None:
        # - start_time
        # - end_time
        # With the following query parameters
        # - created_before
        # - created_after
        # - completed_before
        # - completed_after
        job_list = []
        for status_iter in push_query_parameters.status_list:
            job_list += list(PushJobData.query(
                A.status == status_iter,
                filter_condition=filter_expression,
                index="status-index",
                load_full_item=True
            ))
    else:
        job_list = list(PushJobData.scan(
            filter_condition=filter_expression,
            load_full_item=True
        ))

    return PushJobQueryPaginatedResponse.from_results_list(
        results=list(map(
            lambda job_iter: job_iter.to_dict(),
            job_list
        )),
        query_pagination=pagination,
        params_response=dict(filter(
            lambda kv: kv[1] is not None,
            dict(
                **push_query_parameters.to_params_dict(),
                **pagination
            ).items()
        )),
    )


# Get a package from orcabus id
@router.get(
    "/{push_job_id}",
    tags=["push job query"],
    description="Get a job object"
)
async def get_push_jobs(package_id: str = Depends(sanitise_psh_orcabus_id)) -> PushJobResponse:
    try:
        return PushJobData.get(package_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/{push_job_id}",
    tags=["push job update"],
    description=dedent("""
    Update a job status. This will update a job and set the status to the new status.
    This is internal use only and should only be used by the job execution step function.
    """)
)
async def update_job(
        push_job_id: str = Depends(sanitise_psh_orcabus_id),
        push_job_status_obj: Annotated[JobPatch, Body()] = get_default_job_patch_entry()
) -> PushJobResponse:
    if push_job_status_obj.status not in [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.SUCCEEDED]:
        raise HTTPException(status_code=400, detail="Invalid status provided, must be one of RUNNING, FAILED or COMPLETED")
    try:
        push_job_obj = PushJobData.get(push_job_id)
        push_job_obj.status = push_job_status_obj.status

        # If status is in a terminal state, set the end time
        if push_job_obj.status in [JobStatus.FAILED, JobStatus.SUCCEEDED]:
            push_job_obj.end_time = datetime.now(timezone.utc)

        push_job_obj.save()
        job_dict = push_job_obj.to_dict()
        put_push_job_update_event(job_dict)
        return job_dict
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{push_job_id}:abort",
    tags=["push job update"],
    description=dedent("""
    Abort a package job. This will abort a job and set the status to ABORTED
    """)
)
async def abort_job(push_job_id: str = Depends(sanitise_psh_orcabus_id)) -> PushJobResponse:
    try:
        push_job_obj = PushJobData.get(push_job_id)

        if not push_job_obj.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise AssertionError("Job is not in a state that can be aborted")

        push_job_obj.status = JobStatus.ABORTED

        # Abort the execution arn
        abort_sfn(push_job_obj.steps_execution_arn)

        push_job_obj.save()

        push_job_obj_dict = push_job_obj.to_dict()

        put_push_job_update_event(push_job_obj_dict)

        return push_job_obj_dict
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





