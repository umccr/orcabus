#!/usr/bin/env python3

"""
Routes for the API V1 Fastq endpoint

# TODO - fix issue that allows requests API to query an attribute multiple times, i.e instrumentRunId[]=[abcde,defgh]

This is the list of routes available
- GET /fastq  (requires at least one of index, lane, library_id or instrument_run_id)
- POST /fastq  Create a fastq
- GET /fastq/{fastq_id}
- GET /fastq/{fastq_id}/toFastqListRow
- GET /fastq/{fastq_id}/presign

# Workflow based updates
- PATCH /fastq/{fastq_id}:runQcStats
- PATCH /fastq/{fastq_id}:runNtsm
- PATCH /fastq/{fastq_id}:runFileCompressionInfo
- GET /fastq/{fastq_id}/jobs

# Manual updates
- PATCH /fastq/{fastq_id}/addQcStats
- PATCH /fastq/{fastq_id}/addReadCount
- PATCH /fastq/{fastq_id}/addFileCompressionInformation
- PATCH /fastq/{fastq_id}/addNtsmStorageObject
- PATCH /fastq/{fastq_id}/invalidate
- PATCH /fastq/{fastq_id}/validate
- PATCH /fastq/{fastq_id}/addFastqPairStorageObject
- PATCH /fastq/{fastq_id}/detachFastqPairStorageObject
- DELETE /fastq/{fastq_id}

"""
# Standard imports
import json
from operator import concat
from textwrap import dedent
from typing import Optional, Dict
from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist
from functools import reduce
from itertools import product

# Import metadata tools
from metadata_tools import (
    get_library_orcabus_id_from_library_id
)
from . import run_and_save_fastq_list_row_job, get_pagination_params
from ....events.events import put_fastq_list_row_update_event
from ....globals import FastqListRowStateChangeStatusEventsEnum

# Model imports
from ....models import BoolQueryEnum, FastqListRowDict, PresignedUrlModel, QueryPagination
from ....models.fastq_list_row import (
    FastqListRowData, FastqListRowCreate,
    FastqListRowListResponse, FastqListRowQueryPaginatedResponse, FastqListRowResponseDict
)
from ....models.fastq_pair import FastqPairStorageObjectPatch, FastqPairStorageObjectData
from ....models.fastq_set import FastqSetData
from ....models.file_compression_info import FileCompressionInfoPatch, FileCompressionInfoData
from ....models.job import JobType, JobData, JobResponse, JobQueryPaginatedResponse
from ....models.library import LibraryData, LibraryPatch
from ....models.ntsm import NtsmUriUpdate, NtsmUriData
from ....models.qc import QcInformationPatch, QcInformationData
from ....models.query import LabMetadataQueryParameters, InstrumentQueryParameters, FastqSetIdQueryParameters
from ....models.read_count_info import ReadCountInfoPatch, ReadCountInfoData
from ....utils import (
    is_orcabus_ulid,
    sanitise_fqr_orcabus_id
)

router = APIRouter()


## Query options
@router.get(
    "", tags=["fastq query"],
    description=dedent("""
Get a list of FastqListRow objects.<br>
You must specify any of the following combinations:<br>
<ul> 
    <li>index + lane + instrumentRunId (this will get you exactly one response)</li>
    <li>index + instrumentRunId (this will get you exactly one response)</li>
    <li>lane + instrumentRunId (this will get you exactly one response)</li>
    <li>instrumentRunId</li>
    <li>one of [library, sample, subject, individual, project]</li>
    <li>one of [library, sample, subject, individual, project] and instrumentRunId</li>
</ul>    

This means you cannot<br>
<ul>
    <li>Specify index or lane without specifying instrumentRunId</li>
    <li>Specify multiple metadata attributes</li>
    <li>Specify zero parameters</li>
</ul>

You may query multiple instrumentRunIds and metadata attributes using the <code>[]</code> syntax.<br> 

For example, to query multiple libraries, use <code>library[]=L12345&library[]=L123456</code>
""")
)
async def list_fastq(
        # Lab metadata options
        lab_metadata_query_parameters: LabMetadataQueryParameters = Depends(),
        # Instrument query options
        instrument_query_parameters: InstrumentQueryParameters = Depends(),
        # Fastq Set query options
        fastq_set_query_parameters: FastqSetIdQueryParameters = Depends(),
        # Filter query
        valid: Optional[BoolQueryEnum] = BoolQueryEnum.TRUE,
        # Include s3 uri - resolve the s3 uri if requested
        include_s3_details: Optional[bool] = Query(
            default=False,
            alias="includeS3Details",
            description="Include the s3 details such as s3 uri and storage class"
        ),
        # Pagination
        pagination: QueryPagination = Depends(get_pagination_params),
) -> FastqListRowQueryPaginatedResponse:
    # Convert valid to BoolQueryEnum
    valid = BoolQueryEnum(valid)

    # Check boolean parameters
    if valid == BoolQueryEnum.ALL:
        filter_expression = None
    else:
        filter_expression = A.is_valid == json.loads(valid.value)

    # Set library list for lab metadata query
    lab_metadata_query_parameters.set_library_list_from_query()

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [
        fastq_set_query_parameters.fastq_set_id_list,
        lab_metadata_query_parameters.library_list,
        instrument_query_parameters.instrument_run_id_list
    ])):
        raise HTTPException(
            status_code=400,
            detail="At least one of fastqSetId, libraryId or instrumentRunId is required"
        )

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []

    # We can generate rgids given the index and lane
    if instrument_query_parameters.index_list is not None and instrument_query_parameters.lane_list is not None:
        # Generate the rgid from the index and lane
        # Note that this cross product of indexes and lanes
        # BUT we can query the rgid_ext directly
        rgid_ext_list = list(map(
            lambda rgid_iter_: ".".join(map(str, rgid_iter_)),
            list(product(
                instrument_query_parameters.index_list,
                instrument_query_parameters.lane_list,
                instrument_query_parameters.instrument_run_id_list
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
    elif instrument_query_parameters.index_list is not None:
        # We can use a filter expression to query the index
        filter_expression = filter_expression & A.index.is_in(instrument_query_parameters.index_list)
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
                    instrument_query_parameters.instrument_run_id_list
                ))
            ))
        )
    elif instrument_query_parameters.lane_list is not None:
        # We can use a filter expression to query the lane
        filter_expression = filter_expression & A.lane.is_in(instrument_query_parameters.lane_list)
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
                    instrument_query_parameters.instrument_run_id_list
                ))
            ))
        )
    elif instrument_query_parameters.instrument_run_id_list is not None:
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
                    instrument_query_parameters.instrument_run_id_list
                ))
            ))
        )

    # Set library list query
    if lab_metadata_query_parameters.library_list is not None:
        library_orcabus_ids = list(map(
            lambda library_id_iter_: (
                library_id_iter_ if is_orcabus_ulid(library_id_iter_)
                else get_library_orcabus_id_from_library_id(library_id_iter_)
            ),
            lab_metadata_query_parameters.library_list
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

    if fastq_set_query_parameters.fastq_set_id_list is not None:
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
                    fastq_set_query_parameters.fastq_set_id_list
                ))
            ))
        )

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return FastqListRowQueryPaginatedResponse.from_results_list(
            results=FastqListRowListResponse(
                fastq_list_rows=list(map(
                    lambda fqlr_iter_: fqlr_iter_.to_dict(),
                    query_lists[0]
                )),
                include_s3_details=include_s3_details
            ).model_dump(),
            query_pagination=pagination,
            params_response=dict(filter(
                lambda kv: kv[1] is not None,
                dict(
                    **lab_metadata_query_parameters.to_params_dict(),
                    **instrument_query_parameters.to_params_dict(),
                    **fastq_set_query_parameters.to_params_dict(),
                    **{
                        "valid": valid.value,
                    },
                    **{
                        "includeS3Details": include_s3_details,
                    },
                    **pagination
                ).items()
            )),
        )

    # Else query list is greater than one
    # Bind on the id
    fqr_orcabus_ids = set(map(lambda fqlr_iter_: fqlr_iter_.id, query_lists[0]))
    # For each list reduce to the fqr orcabus that match the previous set
    for query_list in query_lists[1:]:
        fqr_orcabus_ids = fqr_orcabus_ids.intersection(
            set(map(lambda fqlr_iter_: fqlr_iter_.id, query_list))
        )

    # Now we have our fqr_orcabus_ids, we can get the FastqListRow objects
    return FastqListRowQueryPaginatedResponse.from_results_list(
        results=FastqListRowListResponse(
            fastq_list_rows=list(map(
                lambda fqlr_iter_: fqlr_iter_.to_dict(),
                filter(
                    lambda fq_iter_: fq_iter_.id in fqr_orcabus_ids,
                    query_lists[0]
                )
            )),
            include_s3_details=include_s3_details
        ).model_dump(by_alias=True),
        query_pagination=pagination,
        params_response=dict(filter(
            lambda kv: kv[1] is not None,
            dict(
                **lab_metadata_query_parameters.to_params_dict(),
                **instrument_query_parameters.to_params_dict(),
                **fastq_set_query_parameters.to_params_dict(),
                **{
                    "valid": valid.value,
                },
                **{
                    "includeS3Details": include_s3_details,
                },
                **pagination
            ).items()
        )),
    )


# Get a fastq from orcabus id
@router.get(
    "/{fastq_id}",
    tags=["fastq query"],
    description="Get a Fastq List Row Object by its orcabus id, 'fqr.' prefix is optional"
)
async def get_fastq(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        # Include s3 uri - resolve the s3 uri if requested
        include_s3_details: Optional[bool] = Query(
            default=False,
            alias="includeS3Details",
            description="Include the s3 details such as s3 uri and storage class"
        ),
) -> FastqListRowResponseDict:
    try:
        return FastqListRowData.get(fastq_id).to_dict(
            include_s3_details=include_s3_details
        )
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
async def create_fastq(fastq_obj: FastqListRowCreate) -> FastqListRowResponseDict:
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

    # Write fastq dict
    fastq_dict = fastq_obj.to_dict()
    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_CREATED
    )

    # Return the fastq as a dictionary
    return fastq_dict


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
async def update_library(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        library_obj: LibraryPatch = Depends()
) -> FastqListRowResponseDict:
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

    fastq_obj_dict = fastq_obj.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_obj_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.LIBRARY_UPDATED
    )

    # Return the fastq to dictionary
    return fastq_obj_dict


@router.get(
    "/{fastq_id}/presign",
    tags=["fastq download"],
    description="Get a presigned url for the fastq files pair"
)
async def get_presigned_url(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> PresignedUrlModel:
    return FastqListRowData.get(fastq_id).presign_uris()


# - PATCH /fastq/{fastq_id}:runQcStats
@router.patch(
    "/{fastq_id}:runQcStats",
    tags=["fastq workflow"]
)
async def run_qc_stats(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> JobResponse:
    return run_and_save_fastq_list_row_job(fastq_id, JobType.QC)


# - PATCH /fastq/{fastq_id}:runNtsm
@router.patch(
    "/{fastq_id}:runNtsm",
    tags=["fastq workflow"]
)
async def run_qc_stats(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> JobResponse:
    return run_and_save_fastq_list_row_job(fastq_id, JobType.NTSM)


# - PATCH /fastq/{fastq_id}:runFileCompressionInformation
@router.patch(
    "/{fastq_id}:runFileCompressionInformation",
    tags=["fastq workflow"]
)
async def run_qc_stats(fastq_id: str = Depends(sanitise_fqr_orcabus_id)) -> JobResponse:
    return run_and_save_fastq_list_row_job(fastq_id, JobType.FILE_COMPRESSION)


# - Get /jobs endpoint for a given fastq list row id
@router.get(
    "/{fastq_id}/jobs",
    tags=["fastq workflow"]
)
async def get_jobs(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        # Pagination options
        pagination: Dict = Depends(get_pagination_params),
) -> JobQueryPaginatedResponse:
    return JobQueryPaginatedResponse.from_results_list(
        results=list(map(
            lambda job_iter_: job_iter_.to_dict(),
            list(JobData.query(
                A.fastq_id == fastq_id,
                index="fastq_id-index",
                load_full_item=True
            ))
        )),
        query_pagination=pagination,
        params_response={
            "fastqId": fastq_id,
        },
        # For get_fastq url
        fastq_id=fastq_id,
    )


# PATCHES
@router.patch(
    "/{fastq_id}/addQcStats",
    tags=["fastq update"],
    description="Add QC Stats to a Fastq List Row Object"
)
async def add_qc_stats(fastq_id: str = Depends(sanitise_fqr_orcabus_id),
                       qc_obj: QcInformationPatch = Depends()) -> FastqListRowResponseDict:
    fastq_obj = FastqListRowData.get(fastq_id)
    fastq_obj.qc = QcInformationData(**dict(qc_obj.model_dump(by_alias=True)))
    fastq_obj.save()

    # Create dict
    fastq_obj_dict = fastq_obj.to_dict()

    # Put update event into the ethos
    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_obj_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.QC_UPDATED
    )

    # Return the fastq as a dictionary
    return fastq_obj_dict


@router.patch(
    "/{fastq_id}/addReadCount",
    tags=["fastq update"],
    description="Add Read Count Information to a Fastq List Row Object"
)
async def add_read_count(fastq_id: str = Depends(sanitise_fqr_orcabus_id),
                         read_count_obj: ReadCountInfoPatch = Depends()) -> FastqListRowResponseDict:
    fastq = FastqListRowData.get(fastq_id)

    # Get read count info
    read_count_info_data = ReadCountInfoData(**dict(read_count_obj.model_dump(by_alias=True)))

    # Update attributes
    fastq.read_count = read_count_info_data.read_count
    fastq.base_count_est = read_count_info_data.base_count_est

    fastq.save()

    # Generate fastq object as a dict
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.READ_COUNT_UPDATED
    )

    return fastq_dict


@router.patch(
    "/{fastq_id}/addFileCompressionInformation",
    tags=["fastq update"],
    description="Add File Compression Information to a Fastq List Row Object"
)
async def add_file_compression(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        file_compression_obj: FileCompressionInfoPatch = Depends()
) -> FastqListRowResponseDict:
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
    fastq.read_set.r1.raw_md5sum = file_compression_info_data.r1_raw_md5sum

    if fastq.read_set.r2 is not None:
        fastq.read_set.r2.gzip_compression_size_in_bytes = file_compression_info_data.r2_gzip_compression_size_in_bytes
        fastq.read_set.r2.raw_md5sum = file_compression_info_data.r2_raw_md5sum

    fastq.save()

    # Generate fastq object as a dict with s3 details
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.FILE_COMPRESSION_UPDATED
    )

    return fastq_dict


@router.patch(
    "/{fastq_id}/addNtsmStorageObject",
    tags=["fastq update"],
    description="Add Ntsm Storage Object to a Fastq List Row Object"
)
async def add_ntsm_uri(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        ntsm: NtsmUriUpdate = Depends()
) -> FastqListRowResponseDict:
    fastq = FastqListRowData.get(fastq_id)
    fastq.ntsm = NtsmUriData(**dict(ntsm.model_dump())).ntsm
    fastq.save()

    fastq.save()

    # Generate fastq object as a dict with s3 details
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.NTSM_UPDATED
    )

    return fastq_dict


# Validation
@router.patch(
    "/{fastq_id}/validate",
    tags=["fastq validate"],
    description="Validate a Fastq List Row Object"
)
async def validate_fastq(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id)
) -> FastqListRowResponseDict:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = True
    fastq.save()

    # Generate fastq object as a dict with s3 details
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_IS_VALID
    )

    return fastq_dict


@router.patch(
    "/{fastq_id}/invalidate",
    tags=["fastq validate"],
    description="Invalidate a Fastq List Row Object, this is useful if an instrument run has failed"
)
async def invalidate_fastq(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id)
) -> FastqListRowResponseDict:
    fastq_obj = FastqListRowData.get(fastq_id)

    # Check if the fastq is part of a fastq set
    if fastq_obj.fastq_set_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot invalidate a fastq that is part of a fastq set, please first unlink and then invalidate"
        )

    fastq_obj.is_valid = False
    fastq_obj.save()

    # Generate fastq object as a dict with s3 details
    fastq_dict = fastq_obj.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_IS_INVALID
    )

    return fastq_dict


@router.patch(
    "/{fastq_id}/addFastqPairStorageObject",
    tags=["fastq update"],
    description="Add Fastq Pair Storage Object to a Fastq List Row Object"
)
async def add_fastq_pair_storage_object(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id),
        fastq_pair_storage_obj: FastqPairStorageObjectPatch = Depends()
) -> FastqListRowResponseDict:
    fastq = FastqListRowData.get(fastq_id)
    # Check that no fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.read_set is None, "A FastqPairStorageObject already exists for this fastq, please detach it first"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.read_set = FastqPairStorageObjectData(**dict(fastq_pair_storage_obj.model_dump(by_alias=True)))
    fastq.save()

    # Generate fastq object as a dict with s3 details
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.READ_SET_ADDED
    )

    return fastq_dict


@router.patch(
    "/{fastq_id}/detachFastqPairStorageObject",
    tags=["fastq update"],
    description="Remove Fastq Pair Storage Object from a Fastq List Row Object"
)
async def remove_fastq_pair_storage_object(
        fastq_id: str = Depends(sanitise_fqr_orcabus_id)
) -> FastqListRowResponseDict:
    fastq = FastqListRowData.get(fastq_id)
    # Check that the fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.read_set is not None, "no FastqPairStorageObject does not exists for this fastq"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.read_set = None
    fastq.save()

    # Generate fastq object as a dict
    fastq_dict = fastq.to_dict()

    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.READ_SET_DELETED
    )

    return fastq_dict


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

    put_fastq_list_row_update_event(
        fastq_list_row_response_object={"fastqId": fastq_obj.id},
        event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_DELETED
    )

    return {"status": "ok"}
