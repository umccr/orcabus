#!/usr/bin/env python3

"""

# TODO - add query params, sort by, pagination
# TODO - add lambda function to launch step function

Routes for the API V1 Fastq endpoint

This is the list of routes available
-

"""
# Standard imports
import json
from operator import concat
from textwrap import dedent
from typing import List, Optional, Dict
from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist
from functools import reduce
from itertools import product

from api.fastq_manager_api_tools.models.file_compression_info import FileCompressionInfoPatch, FileCompressionInfoData

from api.fastq_manager_api_tools.models.fastq_list_row import FastqListRowResponse, FastqListRowData

from api.fastq_manager_api_tools.utils import sanitise_fqr_orcabus_id

from api.fastq_manager_api_tools.models.ntsm import NtsmUriUpdate, NtsmUriData
# Import metadata tools
from metadata_tools import (
    get_library_orcabus_id_from_library_id
)

# Model imports
from ...models import JobStatus, JobQueryResponse, QueryPagination

router = APIRouter()


# Define a dependency function that returns the pagination parameters
def get_pagination_params(
    # page must be greater than or equal to 0
    page: int = Query(0, ge=0),
    # rowsPerPage must be greater than 0
    rows_per_page: int = Query(100, gt=0, alias='rowsPerPage')
) -> QueryPagination:
    return {"page": page, "rowsPerPage": rows_per_page}


## Query options
@router.get(
    "",
    tags=["job query"],
    description=dedent("""
Get a list of job objects, you can filter by the following parameters:
    * startTime (optional) - start time of the job
    * endTime (optional) - end time of the job
    * status (optional) - status of the job
"""),
)
async def list_jobs(
        # Status
        status: Optional[JobStatus] = Query(
            None,
            description="The status to query on"
        ),
        # Start time
        min_start_time: Optional[str] = Query(
            None,
            description="The minimum start time to query on. Jobs started before this date will be excluded"
        ),
        max_start_time: Optional[str] = Query(
            None,
            description="The maximum start time to query on. Jobs started after this date will be excluded"
        ),
        # End time
        min_end_time: Optional[str] = Query(
            None,
            description="The minimum end time to query on. Jobs ended before this date will be excluded"
        ),
        max_end_time: Optional[str] = Query(
            None,
            description="The maximum end time to query on. Jobs ended after this date will be excluded"
        ),
        # Pagination options
        pagination: Dict = Depends(get_pagination_params),
) -> JobQueryResponse:
    valid = BoolQueryEnum(valid)
    # Check boolean parameters
    if valid == BoolQueryEnum.ALL:
        filter_expression = None
    else:
        filter_expression = A.is_valid == json.loads(valid.value)

    # Confirm that only one metadata attribute has been specified
    if len(
        list(filter(
            lambda x: x is not None, [
                library, library_list,
                sample, sample_list,
                subject, subject_list,
                individual, individual_list,
                project, project_list
            ]
        ))
    ) > 1:
        raise HTTPException(
            status_code=400,
            detail="Only one of library, sample, subject, individual or project is allowed"
        )
    # Convert the metadata attribute to a library list
    library_list = get_libraries_from_metadata_query(
        library, library_list,
        sample, sample_list,
        subject, subject_list,
        individual, individual_list,
        project, project_list
    )

    # Check only one of index and index_list is specified
    if index is not None and index_list is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of index or index[] is allowed"
        )
    if index is not None:
        index_list = [index]

    # Check only of lane and lane_list is specified
    if lane is not None and lane_list is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of lane or lane[] is allowed"
        )
    if lane is not None:
        lane_list = [lane]

    # Check only one of instrument_run_id_list and instrument_run_id is specified
    if instrument_run_id is not None and instrument_run_id_list is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of instrumentRunId or instrumentRunId[] is allowed"
        )
    if instrument_run_id is not None:
        instrument_run_id_list = [instrument_run_id]

    # Check only one of fastq_set_id_list and fastq_set_id is specified
    if fastq_set_id is not None and fastq_set_id_list is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of fastqSetId or fastqSetId[] is allowed"
        )
    if fastq_set_id is not None:
        fastq_set_id_list = [fastq_set_id]

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [
        fastq_set_id_list,
        library_list,
        instrument_run_id_list
    ])):
        raise HTTPException(
            status_code=400,
            detail="At least one of fastqSetId, libraryId or instrumentRunId is required"
        )

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []
    if index_list is not None and instrument_run_id_list is None:
        raise HTTPException(
            status_code=400,
            detail="instrumentRunId is required if index is provided"
        )
    if lane_list is not None and instrument_run_id_list is None:
        raise HTTPException(
            status_code=400,
            detail="instrumentRunId is required if lane is provided"
        )

    # We can generate rgids given the index and lane
    if index_list is not None and lane_list is not None:
        # Generate the rgid from the index and lane
        # Note that this cross product of indexes and lanes
        # BUT we can query the rgid_ext directly
        rgid_ext_list = list(map(
            lambda rgid_iter_: ".".join(map(str, rgid_iter_)),
            list(product(
                index_list,
                lane_list,
                instrument_run_id_list
            ))
        ))
        query_lists.append(
            list(reduce(
                concat,
                list(map(
                    lambda rgid_ext_iter_: (
                        list(FastqListRowData.query(
                            A.rgid_ext == rgid_ext_iter_,
                            filter_condition=filter_expression,
                            index="rgid_ext-index",
                            load_full_item=True
                        ))
                    ),
                    rgid_ext_list
                ))
            ))
        )
    elif index_list is not None:
        # We can use a filter expression to query the index
        filter_expression = filter_expression & A.index.is_in(index_list)
        query_lists.append(
            list(reduce(
                concat,
                list(map(
                    lambda instrument_run_id_iter_: (
                        list(FastqListRowData.query(
                            A.instrument_run_id == instrument_run_id_iter_,
                            filter_condition=filter_expression,
                            index="instrument_run_id-index",
                            load_full_item=True
                        ))
                    ),
                    instrument_run_id_list
                ))
            ))
        )
    elif lane_list is not None:
        # We can use a filter expression to query the lane
        filter_expression = filter_expression & A.lane.is_in(lane_list)
        query_lists.append(
            list(reduce(
                concat,
                list(map(
                    lambda instrument_run_id_iter_: (
                        list(FastqListRowData.query(
                            A.instrument_run_id == instrument_run_id_iter_,
                            filter_condition=filter_expression,
                            index="instrument_run_id-index",
                            load_full_item=True
                        ))
                    ),
                    instrument_run_id_list
                ))
            ))
        )
    elif instrument_run_id_list is not None:
        query_lists.append(
            list(reduce(
                concat,
                list(map(
                    lambda instrument_run_id_iter_: (
                        list(FastqListRowData.query(
                            A.instrument_run_id == instrument_run_id_iter_,
                            filter_condition=filter_expression,
                            index="instrument_run_id-index",
                            load_full_item=True
                        ))
                    ),
                    instrument_run_id_list
                ))
            ))
        )

    # Set library list query
    if library_list is not None:
        library_orcabus_ids = list(map(
            lambda library_id_iter_: (
                library_id_iter_ if is_orcabus_ulid(library_id_iter_)
                else get_library_orcabus_id_from_library_id(library_id_iter_)
            ),
            library_list
        ))

        query_lists.append(
            # Need to flatten list, might be multiple queries
            list(reduce(
                concat,
                list(map(
                    lambda library_orcabus_id_iter_: (
                        list(FastqListRowData.query(
                            A.library_orcabus_id == library_orcabus_id_iter_,
                            filter_condition=filter_expression,
                            index="library_orcabus_id-index",
                            load_full_item=True
                        ))
                    ),
                    library_orcabus_ids
                ))
            ))
        )

    if fastq_set_id_list is not None:
        query_lists.append(
            # Need to flatten list, might be multiple queries
            list(reduce(
                concat,
                list(map(
                    lambda fastq_set_id_iter: (
                        list(FastqListRowData.query(
                            A.fastq_set_id == fastq_set_id_iter,
                            filter_condition=filter_expression,
                            index="fastq_set_id-index",
                            load_full_item=True
                        ))
                    ),
                    fastq_set_id_list
                ))
            ))
        )

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return FastqListRowListResponse(
            fastq_list_rows=list(map(
                lambda fqlr_iter_: fqlr_iter_.to_dict(),
                query_lists[0]
            )),
            include_s3_details=include_s3_details
        ).model_dump()

    # Else query list is greater than one
    # Bind on the id
    fqr_orcabus_ids = set(map(lambda fqlr_iter_: fqlr_iter_.id, query_lists[0]))
    # For each list reduce to the fqr orcabus that match the previous set
    for query_list in query_lists[1:]:
        fqr_orcabus_ids = fqr_orcabus_ids.intersection(
            set(map(lambda fqlr_iter_: fqlr_iter_.id, query_list))
        )

    # Now we have our fqr_orcabus_ids, we can get the FastqListRow objects
    return FastqListRowListResponse(
        fastq_list_rows=list(map(
            lambda fqlr_iter_: fqlr_iter_.to_dict(),
            filter(
                lambda fq_iter_: fq_iter_.id in fqr_orcabus_ids,
                query_lists[0]
            )
        )),
        include_s3_details=include_s3_details
    ).model_dump(by_alias=True)


# Get a fastq from orcabus id
@router.get(
    "/{fastq_id}",
    tags=["fastq query"],
    description="Get a Fastq List Row Object by its orcabus id, 'fqr.' prefix is optional"
)
async def get_fastq(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> FastqListRowResponse:
    try:
        return FastqListRowData.get(fastq_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# Create a fastq object
@router.post(
    "",
    tags=["fastq create"],
    description=dedent("""
    Create a Fastq List Row Object, you will need to make sure that the index + lane + instrument run id is unique. "
    Please use the fastqSet endpoint if registering multiple fastqs simultaneously to reduce race conditions
    """)
)
async def create_fastq(fastq_obj: FastqListRowCreate) -> FastqListRowResponse:
    # First convert the CreateFastqListRow to a FastqListRow
    fastq_obj = FastqListRowData(**dict(fastq_obj.model_dump(by_alias=True)))

    # # Check if the fastq already exists
    try:
        assert len(list(FastqListRowData.query(
            A.rgid_ext == fastq_obj.rgid_ext,
            index="rgid_ext-index",
            load_full_item=True
        ))) == 0, f"Fastq with index.lane.instrumentRunId '{fastq_obj.rgid_ext}' already exists"
    except AssertionError as e:
        # Return a 409 Conflict if the fastq already exists
        raise HTTPException(status_code=409, detail=str(e))

    # Save the fastq
    fastq_obj.save()

    # Return the fastq as a dictionary
    return fastq_obj.to_dict()


# MODIFIED GETS
@router.get(
    "/{fastq_id}/toFastqListRow",
    tags=["fastq workflow"],
    description="Return in fastq list row format"
)
async def get_fastq_list_row(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> FastqListRowDict:
    return FastqListRowData.get(fastq_id).to_fastq_list_row()


@router.patch(
    "/{fastq_id}/updateLibrary",
    tags=["fastq update"],
    description="Update the library associated with a Fastq List Row Object"
)
async def update_library(fastq_id: str = Depends(sanitise_fqr_orcabus_id), library_obj: LibraryPatch = Depends()) -> FastqListRowResponse:
    fastq_obj = FastqListRowData.get(fastq_id)

    library_obj = LibraryData(**dict(library_obj.model_dump(by_alias=True)))

    if fastq_obj.fastq_set_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot update library for a fastq that is part of a fastq set, please first unlink and then update library"
        )

    # Update the library object
    fastq_obj.library = library_obj

    # Save the fastq object
    fastq_obj.save()

    # Return the fastq to dictionary
    return fastq_obj.to_dict()


@router.get(
    "/{fastq_id}/presign",
    tags=["fastq download"],
    description="Get a presigned url for the fastq files pair"
)
async def get_presigned_url(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> PresignedUrlModel:
    return FastqListRowData.get(fastq_id).presign_uris()


# PATCHES
@router.patch(
    "/{fastq_id}/addQcStats",
    tags=["fastq update"],
    description="Add QC Stats to a Fastq List Row Object"
)
async def add_qc_stats(fastq_id: str = Depends(sanitise_fqr_orcabus_id), qc_obj: QcInformationPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.qc = QcInformationData(**dict(qc_obj.model_dump(by_alias=True)))
    fastq.save()
    return fastq.to_dict()

@router.patch(
    "/{fastq_id}/addReadCount",
    tags=["fastq update"],
    description="Add Read Count Information to a Fastq List Row Object"
)
async def add_read_count(fastq_id: str = Depends(sanitise_fqr_orcabus_id), read_count_obj: ReadCountInfoPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)

    # Get read count info
    read_count_info_data = ReadCountInfoData(**dict(read_count_obj.model_dump(by_alias=True)))

    # Update attributes
    fastq.read_count = read_count_info_data.read_count
    fastq.base_count_est = read_count_info_data.base_count_est

    fastq.save()
    return fastq.to_dict()

@router.patch(
    "/{fastq_id}/addFileCompressionInformation",
    tags=["fastq update"],
    description="Add File Compression Information to a Fastq List Row Object"
)
async def add_file_compression(fastq_id: str = Depends(sanitise_fqr_orcabus_id), file_compression_obj: FileCompressionInfoPatch = Depends()) -> FastqListRowResponse:
    # Get fastq object
    fastq = FastqListRowData.get(fastq_id)

    # Read in file compression data
    file_compression_info_data = FileCompressionInfoData(**dict(file_compression_obj.model_dump(by_alias=True)))

    # Assert that files is not None
    try:
        assert fastq.read_set is not None, "No FastqPairStorageObject exists for this fastq, cannot add compression information"
    except AssertionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Add compression info
    fastq.read_set.compression_format = file_compression_info_data.compression_format
    fastq.read_set.r1.gzip_compression_size_in_bytes = file_compression_info_data.r1_gzip_compression_size_in_bytes
    fastq.read_set.r2.gzip_compression_size_in_bytes = file_compression_info_data.r2_gzip_compression_size_in_bytes
    fastq.save()
    return fastq.to_dict()


@router.patch(
    "/{fastq_id}/addNtsmStorageObject",
    tags=["fastq update"],
    description="Add Ntsm Storage Object to a Fastq List Row Object"
)
async def add_ntsm_uri(fastq_id: str = Depends(sanitise_fqr_orcabus_id), ntsm: NtsmUriUpdate = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.ntsm = NtsmUriData(**dict(ntsm.model_dump())).ntsm
    fastq.save()
    return fastq.to_dict()


# Validation
@router.patch(
    "/{fastq_id}/validate",
    tags=["fastq validate"],
    description="Validate a Fastq List Row Object"
)
async def validate_fastq(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = True
    fastq.save()
    return fastq.to_dict()


@router.patch(
    "/{fastq_id}/invalidate",
    tags=["fastq validate"],
    description="Invalidate a Fastq List Row Object, this is useful if an instrument run has failed"
)
async def invalidate_fastq(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> FastqListRowResponse:
    fastq_obj = FastqListRowData.get(fastq_id)

    # Check if the fastq is part of a fastq set
    if fastq_obj.fastq_set_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot invalidate a fastq that is part of a fastq set, please first unlink and then invalidate"
        )

    fastq_obj.is_valid = False
    fastq_obj.save()
    return fastq_obj.to_dict()


@router.patch(
    "/{fastq_id}/addFastqPairStorageObject",
    tags=["fastq update"],
    description="Add Fastq Pair Storage Object to a Fastq List Row Object"
)
async def add_fastq_pair_storage_object(fastq_id: str = Depends(sanitise_fqr_orcabus_id), fastq_pair_storage_obj: FastqPairStorageObjectPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    # Check that no fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.read_set is None, "A FastqPairStorageObject already exists for this fastq, please detach it first"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.read_set = FastqPairStorageObjectData(**dict(fastq_pair_storage_obj.model_dump(by_alias=True)))
    fastq.save()
    return fastq.to_dict()


@router.patch(
    "/{fastq_id}/detachFastqPairStorageObject",
    tags=["fastq update"],
    description="Remove Fastq Pair Storage Object from a Fastq List Row Object"
)
async def remove_fastq_pair_storage_object(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    # Check that the fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.read_set is not None, "no FastqPairStorageObject does not exists for this fastq"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.read_set = None
    fastq.save()
    return fastq.to_dict()


# DELETE
@router.delete(
    "/{fastq_id}",
    tags=["fastq delete"],
    description="Delete a Fastq List Row Object"
)
async def delete_fastq(fastq_id: str) -> Dict[str, str]:
    # Get the fastq object
    fastq_obj = FastqListRowData.get(fastq_id)

    # Remove the fastq from the current fastq set
    if fastq_obj.fastq_set_id is not None:
        # Ensure that the fastq set id exists? Otherwise we can set to None
        try:
            FastqSetData.get(fastq_obj.fastq_set_id)
            raise HTTPException(
                status_code=409,
                detail="Cannot delete a fastq that is part of a fastq set, please first unlink and then delete"
            )
        except DoesNotExist:
            # If the fastq set id does not exist, then we can delete it
            pass

    fastq_obj.delete()
    return {"status": "ok"}
