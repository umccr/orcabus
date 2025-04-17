#!/usr/bin/env python3

"""
Package API End point

Comprises both the Create and GET API endpoints for creating a data package

We also have the endpoint that allows the user to get the data summary report for a given package job.

Package jobs run asyncronously, events will be generated when a packaging job has completed or failed.

The status of a job can be one of the following:

* PENDING
* RUNNING
* UNARCHIVING
* FAILED
* SUCCEEDED

One can only use the 'presign' or 'push' API endpoints on succeeded packaging jobs.

Once a package has been completed, one can use the following queries to collect information about a package.

# Get requests - programmatic ways to check the data is as intended
api/v1/package/{package_id}/listMetadata
api/v1/package/{package_id}/listFastqs
api/v1/package/{package_id}/listSecondaryAnalyses
api/v1/package/{package_id}/getPackageSummaryReport

# We then add in the ability to presign the package
# This is a post request
api/v1/package/{package_id}:presign

# And then we add in the ability to push the package
# This is also a post request
# This endpoint requires a body with the following format:
{
    "pushLocation": "s3://my-bucket/my-key"
}
api/v1/package/{package_id}:push
"""


# Standard imports
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from textwrap import dedent
from typing import Annotated

from fastapi import Depends, Query, Body
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist

from data_sharing_tools import generate_presigned_url
# Model imports
from ...models.package import (
    PackageCreate, PackageData, PackageQueryPaginatedResponse,
    PackageResponseDict
)
from ...models.push import (
    PushJobData, PushJobResponse, PushJobCreate, PushLocationBody
)

from ...models import QueryPagination, JobStatus, JobPatch
from ...globals import get_default_job_patch_entry, PACKAGE_JOB_STATE_MACHINE_ARN_ENV_VAR, PACKAGE_BUCKET_NAME_ENV_VAR, \
    PRESIGN_STATE_MACHINE_ARN_ENV_VAR, PUSH_JOB_STATE_MACHINE_ARN_ENV_VAR, get_default_push_location_body_entry, \
    get_default_package_create_entry
from ...utils import sanitise_pkg_orcabus_id, launch_sfn, abort_sfn, launch_sync_sfn
from ...events.package import put_package_create_event, put_package_update_event
from ...events.push import put_push_job_create_event
from ...models.query import PackageQueryParameters

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
    tags=["package query"]
)
async def get_packages(
        package_query_parameters: PackageQueryParameters = Depends(),
        # Pagination options
        pagination: QueryPagination = Depends(get_pagination_params),
) -> PackageQueryPaginatedResponse:
    # Package Query Parameters include start time, end time and status
    # We allow for queries by package name and status.

    # Let's try and generate the filter expression
    # We have the following indexed keys in the database (tied to status),
    filter_expression = None
    if package_query_parameters.requested_before is not None:
        filter_expression = filter_expression & (A.request_time <= package_query_parameters.requested_before)
    if package_query_parameters.requested_after is not None:
        filter_expression = filter_expression & (A.request_time >= package_query_parameters.requested_after)
    if package_query_parameters.completed_before is not None:
        filter_expression = filter_expression & (A.completion_time <= package_query_parameters.completed_before)
    if package_query_parameters.completed_after is not None:
        filter_expression = filter_expression & (A.completion_time >= package_query_parameters.completed_after)

    # To query or to scan, depends on if the status is provided
    # Since the status is indexed to the jobs
    if package_query_parameters.package_name_list is not None:
        job_list = []
        for package_name_iter in package_query_parameters.package_name_list:
            job_list += list(PackageData.query(
                A.package_name == package_name_iter,
                filter_condition=filter_expression,
                index="package_name-index",
                load_full_item=True
            ))
    elif package_query_parameters.status_list is not None:
        # - start_time
        # - end_time
        # With the following query parameters
        # - created_before
        # - created_after
        # - completed_before
        # - completed_after
        job_list = []
        for status_iter in package_query_parameters.status_list:
            job_list += list(PackageData.query(
                A.status == status_iter,
                filter_condition=filter_expression,
                index="status-index",
                load_full_item=True
            ))

    else:
        job_list = list(PackageData.scan(
            filter_condition=filter_expression,
            load_full_item=True
        ))

    return PackageQueryPaginatedResponse.from_results_list(
        results=list(map(
            lambda job_iter_: job_iter_.to_dict(),
            job_list
        )),
        query_pagination=pagination,
        params_response=dict(filter(
            lambda kv: kv[1] is not None,
            dict(
                **package_query_parameters.to_params_dict(),
                **pagination
            ).items()
        )),
    )


# Modified gets - get package report
@router.get(
    "/{package_id}:getSummaryReport",
    tags=["package summary"],
    description="Get a report as a presigned url"
)
async def get_report_presigned_url(package_id: str = Depends(sanitise_pkg_orcabus_id)) -> str:
    try:
        package_data = PackageData.get(package_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Ensure that the package status has succeeded
    if not package_data.status == JobStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail="Status is not succeeded")

    # Check that the package has not expired
    if package_data.is_expired():
        raise HTTPException(status_code=409, detail="Package has expired")

    return generate_presigned_url(
        bucket=environ[PACKAGE_BUCKET_NAME_ENV_VAR],
        key=str(Path(package_data.package_s3_sharing_prefix) / "final" / f"SummaryReport.{package_data.package_name}.html")
    )



# Presign the data
@router.get(
    "/{package_id}:presign",
    tags=["package action"],
    description="Generate a presign shell script"
)
async def get_data_presigned_url(package_id: str = Depends(sanitise_pkg_orcabus_id)) -> str:
    try:
        package_data = PackageData.get(package_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Ensure that the package status has succeeded
    if not package_data.status == JobStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail="Status is not succeeded")

    # Check that the package has not expired
    if package_data.is_expired():
        raise HTTPException(status_code=409, detail="Package has expired")

    # Launch the job
    generate_presigned_urls_list_sync = launch_sync_sfn(
        sfn_name=environ[PRESIGN_STATE_MACHINE_ARN_ENV_VAR],
        sfn_input={
            "jobId": package_data.id,
            "packageName": package_data.package_name,
            "packagingS3SharingPrefix": package_data.package_s3_sharing_prefix,
        }
    )

    if not generate_presigned_urls_list_sync['status'] == "SUCCEEDED":
        raise HTTPException(status_code=409, detail=f"Presigned URL maker failed, step function execution id: {generate_presigned_urls_list_sync['name']}")

    return generate_presigned_url(
        bucket=environ[PACKAGE_BUCKET_NAME_ENV_VAR],
        key=str(Path(package_data.package_s3_sharing_prefix) / "final" / f"download-data.{package_data.package_name}.sh")
    )


# Get a package from orcabus id
@router.get(
    "/{package_id}",
    tags=["package query"],
    description="Get a job object"
)
async def get_jobs(package_id: str = Depends(sanitise_pkg_orcabus_id)) -> PackageResponseDict:
    try:
        return PackageData.get(package_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# Create a job object
@router.post(
    "/",
    tags=["package job"],
    description=dedent("""
    Create a new data package for sharing. 
    """)
)
async def create_package(package_obj: Annotated[PackageCreate, Body()] = get_default_package_create_entry()) -> PackageResponseDict:
    # Request itself is not saved
    package_request_dict = package_obj.package_request.model_dump(by_alias=True)

    # Launch the job
    package_obj = PackageData(**dict(package_obj.model_dump(by_alias=True)))
    package_obj.status = JobStatus.PENDING
    package_obj.request_time = datetime.now(timezone.utc)
    package_obj.steps_execution_arn = launch_sfn(
        sfn_name=environ[PACKAGE_JOB_STATE_MACHINE_ARN_ENV_VAR],
        sfn_input={
            "jobId": package_obj.id,
            "packageName": package_obj.package_name,
            "packageQuery": package_request_dict,
            "s3SharingPrefix": package_obj.package_s3_sharing_prefix
        }
    )

    # Save the job object
    # Save the fastq
    package_obj.save()

    # Create the dictionary
    package_dict = package_obj.to_dict()

    # Generate a create event
    put_package_create_event(package_dict)

    # Return the fastq as a dictionary
    return package_dict


@router.patch(
    "/{package_id}:abort",
    tags=["package job"],
    description=dedent("""
    Abort a package job. This will abort a job and set the status to ABORTED
    """)
)
async def abort_job(package_id: str = Depends(sanitise_pkg_orcabus_id)) -> PackageResponseDict:
    try:
        package_obj = PackageData.get(package_id)

        if not package_obj.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise AssertionError("Job is not in a state that can be aborted")

        package_obj.status = JobStatus.ABORTED

        # Abort the execution arn
        abort_sfn(package_obj.steps_execution_arn)

        # Save, event, return
        package_obj.save()
        package_obj_dict = package_obj.to_dict()
        put_package_update_event(package_obj_dict)

        return package_obj_dict
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{package_id}",
    tags=["package job"],
    description=dedent("""
    Update a job status. This will update a job and set the status to the new status.
    This is internal use only and should only be used by the job execution step function.
    """)
)
async def update_job(package_id: str = Depends(sanitise_pkg_orcabus_id), job_status_obj: Annotated[JobPatch, Body()] = get_default_job_patch_entry()) -> PackageResponseDict:
    if job_status_obj.status not in [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.SUCCEEDED]:
        raise HTTPException(status_code=400, detail="Invalid status provided, must be one of RUNNING, FAILED or SUCCEEDED")
    try:
        package_obj = PackageData.get(package_id)
        package_obj.status = job_status_obj.status
        # Check if the status is completed
        if job_status_obj.status == JobStatus.SUCCEEDED:
            package_obj.completion_time = datetime.now(timezone.utc)
        package_obj.save()
        job_dict = package_obj.to_dict()
        put_package_update_event(job_dict)
        return job_dict
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{package_id}",
    tags=["package delete"],
    description=dedent("""
    Delete a package job. This will delete a job object. 
    """)
)
async def delete_job(package_id: str = Depends(sanitise_pkg_orcabus_id)) -> PackageResponseDict:
    try:
        package_obj = PackageData.get(package_id)
        if package_obj.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise AssertionError("Job is in a state that cannot be deleted")
        package_obj.delete()
        return package_obj.to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Push the data
@router.post(
    "/{package_id}:push",
    tags=["package action"],
    description="Push the data to another s3 bucket or icav2 project"
)
async def start_data_push(package_id: str = Depends(sanitise_pkg_orcabus_id), push_location: Annotated[PushLocationBody, Body()] = get_default_push_location_body_entry()) -> PushJobResponse:
    try:
        package_data = PackageData.get(package_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Ensure that the package status has succeeded
    if not package_data.status == JobStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail="Status is not succeeded")

    # Check that the package has not expired
    if package_data.is_expired():
        raise HTTPException(status_code=409, detail="Package has expired")

    # Launch the job
    push_sfn_execution_arn = launch_sfn(
        sfn_name=environ[PUSH_JOB_STATE_MACHINE_ARN_ENV_VAR],
        sfn_input={
            "packagingJobId": package_data.id,
            "packageName": package_data.package_name,
            "packagingS3SharingPrefix": package_data.package_s3_sharing_prefix,
            "destinationUri": push_location.shareDestination
        }
    )

    push_data = PushJobData(**dict(
        PushJobCreate(
            **{
                "stepFunctionsExecutionArn": push_sfn_execution_arn,
                "status": "PENDING",
                "startTime": datetime.now(timezone.utc),
                "packageId": package_data.id,
                "shareDestination": push_location.shareDestination,
            }
        ).model_dump()
    ))

    push_dict = push_data.to_dict()
    put_push_job_create_event(push_dict)
    push_data.save()

    return push_dict
