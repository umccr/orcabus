#!/usr/bin/env python3

"""
This module contains the FastqSet routes for the FastqSet API endpoints

This is the list of routes available
- GET /fastqSet/ - Get the fastq set based on a metadata id and optionally one of the boolean parameters such as
  * currentFastqSet
  * allowAdditionalFastqs which can be set to TRUE, FALSE or ALL
- GET /fastqSet/{fastqSetId} - Get a fastq set object by its orcabus id
- CREATE /fastqSet - Create a list of fastq objects all belonging to the same fastq set id / library
- GET /fastqSet/{fastqSetId}/toFastqListRows - Get fastq list rows for a given fastq set id
- PATCH /fastqSet/{fastqSetId} - Link Fastq add a fastq object to this fastq set
- PATCH /fastqSet/{fastqSetId} - Unlink Fastq remove a fastq object from this fastq set
- PATCH /fastqSet/{fastqSetId}/currentFastqSet - Set as current fastq, all other fastq sets in this library must first be set to FALSE for isCurrent parameter
- PATCH /fastqSet/{fastqSetId}/notCurrentFastqSet - Set as current fastq to false
- PATCH /fastqSet/{fastqSetId}/allowAdditionalFastqs - Allow additional fastqs to this fastq sets, all other fastq sets in this library must first be set to FALSE for this parameter
- PATCH /fastqSet/{fastqSetId}/disallowAdditionalFastqs - Prevent additional fastqs to this fastq sets, all other fastq sets in this library must first be set to FALSE for this parameter
- PATCH /merge - Given multiple fastq set ids, merge these into a single fastq set

- GET /fastqSet/{fastqSetId}:validateNtsmInternal  - Validate the fastq set by running all-by-all on the ntsms in the fastq set
- GET /fastqSet/{fastqSetId}:validateNtsmExternal/{fastqSetId2}  - Compare the fastq set to an external fastq set by running a cross-product on the ntsms in the opposing fastq set.
"""

# Standard imports
import json
from operator import concat
from textwrap import dedent
from typing import List, Optional, Union, Dict
from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist
from functools import reduce

# Import metadata tools
from metadata_tools import (
    get_library_orcabus_id_from_library_id
)
from . import unlink_with_cleanup, run_ntsm_eval, get_pagination_params
from ....events.events import (
    put_fastq_list_row_update_event, put_fastq_set_update_event
)
from ....globals import FastqListRowStateChangeStatusEventsEnum, FastqSetStateChangeStatusEventsEnum

# Model imports
from ....models import BoolQueryEnum, FastqListRowDict, EmptyDict, QueryPagination
from ....models.fastq_list_row import FastqListRowData
from ....models.fastq_set import (
    FastqSetData, FastqSetResponse, FastqSetListResponse, FastqSetCreate,
    FastqSetQueryPaginatedResponse, FastqSetResponseDict
)
from ....models.library import LibraryData
from ....models.merge_fastq_sets import MergePatch
from ....models.query import LabMetadataQueryParameters, InstrumentQueryParameters
from ....utils import (
    is_orcabus_ulid,
    sanitise_fqs_orcabus_id,
    sanitise_fqr_orcabus_id,
    sanitise_fqs_orcabus_id_x,
    sanitise_fqs_orcabus_id_y
)

router = APIRouter()

## Query options
@router.get(
    "", tags=["fastqset query"],
    description=dedent("""
Get a list of FastqListRow objects.<br>
You must specify any of the following combinations:<br>
<ul> 
    <li>library id and current fastq set set to true (this will get you exactly one response)</li>
    <li>instrumentRunId, will return all fastq sets with a library on this instrument run id</li>
    <li>one of [library, sample, subject, individual, project]</li>
    <li>one of [library, sample, subject, individual, project] and instrumentRunId</li>
</ul>    

You may query multiple instrumentRunIds and metadata attributes using the <code>[]</code> syntax.<br> 

For example, to query multiple libraries, use <code>library[]=L12345&library[]=L123456</code>
""")
)
async def list_fastq_sets(
        # Lab metadata options
        lab_metadata_query_parameters: LabMetadataQueryParameters = Depends(LabMetadataQueryParameters),
        # Instrument query options
        instrument_query_parameters: InstrumentQueryParameters = Depends(InstrumentQueryParameters),
        # Filter query
        current_fastq_set: Optional[BoolQueryEnum] = Query(
            default=BoolQueryEnum.TRUE,
            alias="currentFastqSet",
            description="Toggle to return only the current fastq set"
        ),
        allow_additional_fastqs: Optional[BoolQueryEnum] = Query(
            default=BoolQueryEnum.ALL,
            alias="allowAdditionalFastqs",
            description="Toggle to include fastq sets that allow additional fastqs"
        ),
        # Include s3 uri - resolve the s3 uri if requested
        include_s3_details: Optional[bool] = Query(
            default=False,
            alias="includeS3Details",
            description="Include the s3 details such as s3 uri and storage class"
        ),
        # Pagination
        pagination: QueryPagination = Depends(get_pagination_params),
) -> FastqSetQueryPaginatedResponse:
    # Convert the boolean parameters to BoolQueryEnum
    current_fastq_set = BoolQueryEnum(current_fastq_set)
    allow_additional_fastqs = BoolQueryEnum(allow_additional_fastqs)
    # Check boolean parameters
    filter_expression_list = []
    # Append filter expressions for current fastq set collection
    if current_fastq_set == BoolQueryEnum.ALL:
        pass
    else:
        filter_expression_list.append(A.is_current_fastq_set == json.loads(current_fastq_set.value))
    # Append filter expressions for allow additional fastqs
    if allow_additional_fastqs == BoolQueryEnum.ALL:
        pass
    else:
        filter_expression_list.append(A.allow_additional_fastqs == json.loads(allow_additional_fastqs.value))

    # Set library list for lab metadata query
    lab_metadata_query_parameters.set_library_list_from_query()

    # Combine the filter expressions
    if len(filter_expression_list) == 0:
        filter_expression = None
    else:
        filter_expression = filter_expression_list[0]
        for filter_expression_iter_ in filter_expression_list[1:]:
            filter_expression = filter_expression & filter_expression_iter_

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [
        instrument_query_parameters.instrument_run_id_list,
        lab_metadata_query_parameters.library_list,
    ])):
        raise HTTPException(
            status_code=400,
            detail="At least one metadata id (library, sample, subject, individual, project) is required or instrumentRunId"
        )

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []

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
                        list(FastqSetData.query(
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

    if instrument_query_parameters.instrument_run_id_list is not None:
        # First get the fqr data for the instrument run ids
        fastq_list_row_data_in_instrument_run_ids = list(reduce(
            concat,
            list(map(
                lambda instrument_run_id_iter_: (
                    list(FastqListRowData.query(
                        A.instrument_run_id == instrument_run_id_iter_,
                        index="instrument_run_id-index",
                        load_full_item=True
                    ))
                ),
                instrument_query_parameters.instrument_run_id_list
            ))
        ))

        # Get the unique list of fastq set ids
        fastq_set_ids = list(set(list(map(
            lambda fqr_iter_: fqr_iter_.fastq_set_id,
            fastq_list_row_data_in_instrument_run_ids
        ))))

        # Filter the fastq set ids by the filter expressions - current fastq set
        if current_fastq_set != BoolQueryEnum.ALL:
            fastq_set_ids = list(filter(
                lambda fastq_set_id_iter_: FastqSetData.get(fastq_set_id_iter_).is_current_fastq_set == json.loads(current_fastq_set.value),
                fastq_set_ids
            ))
        # Filter the fastq set ids by the filter expressions - allow additional fastqs
        if allow_additional_fastqs != BoolQueryEnum.ALL:
            fastq_set_ids = list(filter(
                lambda fastq_set_id_iter_: FastqSetData.get(fastq_set_id_iter_).allow_additional_fastq == json.loads(allow_additional_fastqs.value),
                fastq_set_ids
            ))

        query_lists.append(
            # Given a list of fastq set ids, get the FastqSetData objects
            list(map(
                lambda fastq_set_id_iter_: FastqSetData.get(fastq_set_id_iter_),
                fastq_set_ids
            ))
        )

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return FastqSetQueryPaginatedResponse.from_results_list(
            results=FastqSetListResponse(
                fastq_set_list=list(map(
                    lambda fqs_iter_: FastqSetData.from_response(**fqs_iter_.to_dict()),
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
                    **{
                        "includeS3Details": include_s3_details,
                        "currentFastqSet": current_fastq_set,
                        "allowAdditionalFastqs": allow_additional_fastqs
                    }
                ).items()
            ))
        )

    # Else query list is greater than one
    # Bind on the id
    fqs_orcabus_ids = set(map(lambda fqs_iter_: fqs_iter_.id, query_lists[0]))
    # For each list reduce to the rgids that match the previous set
    for query_list in query_lists[1:]:
        fqs_orcabus_ids = fqs_orcabus_ids.intersection(
            set(map(lambda fqs_iter_: fqs_iter_.id, query_list))
        )

    # Now we have our fqr_orcabus_ids, we can get the FastqListRow objects
    return FastqSetQueryPaginatedResponse.from_results_list(
        results=FastqSetListResponse(
            fastq_set_list=list(map(
                lambda fqs_iter_: FastqSetData.from_response(**fqs_iter_.to_dict()),
                filter(
                    lambda fq_iter_: fq_iter_.id in fqs_orcabus_ids,
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
                **{
                    "includeS3Details": include_s3_details,
                    "currentFastqSet": current_fastq_set,
                    "allowAdditionalFastqs": allow_additional_fastqs
                }
            ).items()
        ))
    )


# Create a fastq object
@router.post(
    "",
    tags=["fastqset create"],
    description=dedent("""
    Create a Fastq List Set, you will need to make sure that the index + lane + instrument run id is unique for each item in the list"
    Please use the fastqSet endpoint if registering multiple fastqs simultaneously to reduce race conditions
    """)
)
async def create_fastq(fastq_set_obj_create: FastqSetCreate) -> FastqSetResponseDict:
    # Confirm that the library id matches those in the fastq objects
    if len(set(list(map(
        lambda fastq_obj: fastq_obj.library.orcabus_id,
        # Iterate over each object in the fastq set, 'get' object if of type 'string'
        # Otherwise parse the object itself
        list(map(
            lambda fastq_obj_iter_: (
                    FastqListRowData.get(fastq_obj_iter_)
                    if isinstance(fastq_obj_iter_, str)
                    else fastq_obj_iter_
            ),
            fastq_set_obj_create.fastq_set
        ))
    )))) > 1:
        raise HTTPException(
            status_code=409,
            detail="Got multiple different library ids in the fastq objects"
        )

    # Confirm that the library id matches the library id in the fastq set
    first_fastq_obj = fastq_set_obj_create.fastq_set[0]
    if isinstance(first_fastq_obj, str):
        first_fastq_obj = FastqListRowData.get(first_fastq_obj)
    else:
        first_fastq_obj = FastqListRowData(**dict(first_fastq_obj.model_dump(by_alias=True)))

    # Confirm that all fastq sets are unique
    rgid_exts = list(set(list(map(
        lambda fastq_obj_iter_: (
            FastqListRowData.get(fastq_obj_iter_).rgid_ext
            if isinstance(fastq_obj_iter_, str)
            else FastqListRowData(**dict(fastq_obj_iter_.model_dump(by_alias=True))).rgid_ext
        ),
        fastq_set_obj_create.fastq_set
    ))))
    if len(rgid_exts) != len(fastq_set_obj_create.fastq_set):
        raise HTTPException(
            status_code=409,
            detail="Fastq set contains duplicate rgid_exts"
        )

    # Confirm that the fastq objects do not already exist
    has_duplicates = False
    errors = []
    existing_fqr_orcabus_ids = list(filter(
        lambda fastq_list_row_iter_: fastq_list_row_iter_ is not None,
        list(map(
            lambda fastq_set_obj_iter_: (
                fastq_set_obj_iter_
                if isinstance(fastq_set_obj_iter_, str)
                else None
            ),
            fastq_set_obj_create.fastq_set
        ))
    ))
    for rgid_ext_iter_ in rgid_exts:
        for existing_iter in list(FastqListRowData.query(
            A.rgid_ext == rgid_ext_iter_,
            index="rgid_ext-index",
            load_full_item=True
        )):
            if not existing_iter.id in existing_fqr_orcabus_ids:
                has_duplicates = True
                errors.append(f"Fastq with rgid_ext '{rgid_ext_iter_}' already exists")
    if has_duplicates:
        raise HTTPException(
            status_code=409,
            detail="; ".join(map(str, errors))
        )

    # Get library object
    library_obj = LibraryData(**dict(fastq_set_obj_create.library))

    # Check for this library if there is a current fastq set
    if fastq_set_obj_create.is_current_fastq_set:
        # Check if there is a current fastq set in the library
        # Check if there are other fastq sets in the library
        if len(list(FastqSetData.query(
                A.library_orcabus_id == library_obj.orcabus_id,
                filter_condition=(A.is_current_fastq_set == True),
                index="library_orcabus_id-index",
                load_full_item=True
        ))) > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot create fastq set. Another fastq set in library '{fastq_set_obj_create.library.library_id}' is already the current fastq set"
            )
    if fastq_set_obj_create.allow_additional_fastq:
        # Check if there are other fastq sets in the library
        if len(list(FastqSetData.query(
                A.library_orcabus_id == library_obj.orcabus_id,
                filter_condition=(A.allow_additional_fastq == True),
                index="library_orcabus_id-index",
                load_full_item=True
        ))) > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot create fastq set. Another fastq set in library '{fastq_set_obj_create.library.orcabus_id}' is already accepting additional fastqs."
            )

    # Convert fastqset create object to a FastqSetData object
    # For each of the fastq_set objects, convert them from string to FastqListRowData objects
    fastq_data_objs = []
    for fastq_obj_iter_ in fastq_set_obj_create.fastq_set:
        if isinstance(fastq_obj_iter_, str):
            fastq_obj_iter_ = FastqListRowData.get(fastq_obj_iter_)
        else:
            fastq_obj_iter_ = FastqListRowData(**dict(fastq_obj_iter_.model_dump(by_alias=True)))
        fastq_data_objs.append(fastq_obj_iter_)

    # Create the FastqSetData object
    fastq_set_data_obj = FastqSetData(
        library=library_obj,
        allow_additional_fastq=fastq_set_obj_create.allow_additional_fastq,
        is_current_fastq_set=fastq_set_obj_create.is_current_fastq_set,
        fastq_set_ids=list(map(lambda fastq_data_obj_iter_: fastq_data_obj_iter_.id, fastq_data_objs))
    )

    # Check all fastqs are valid
    all_valid = True
    for fastq_obj in fastq_data_objs:
        if not fastq_obj.is_valid:
            all_valid = False
            break
    if not all_valid:
        raise HTTPException(
            status_code=409,
            detail="Fastq set contains invalid fastqs"
        )

    # Ensure that the library id matches the library id in the fastq set
    if fastq_set_data_obj.library.orcabus_id != first_fastq_obj.library.orcabus_id:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set library id does not match those of the fastq objects, "
                   f"{fastq_set_data_obj.library.orcabus_id} != {first_fastq_obj.library.orcabus_id}"
        )

    # Add the fastq_set_id to the fastq objects
    for fastq_obj in fastq_data_objs:
        fastq_obj.fastq_set_id = fastq_set_data_obj.id
        fastq_obj.save()

    # Save the fastq set
    fastq_set_data_obj.save()

    # Generate the fastq set dictionary
    # This will also calculate all of the s3 details for all fastq list rows
    fastq_set_dict = fastq_set_data_obj.to_dict()

    # Add in the create events
    for fastq_obj in fastq_data_objs:
        put_fastq_list_row_update_event(
            fastq_list_row_response_object=fastq_obj.to_dict(),
            event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_CREATED
        )

    # Add in the fastq set created event
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_CREATED,
    )

    # Return the fastq as a dictionary
    return fastq_set_dict


# Direct Get
@router.get(
    "/{fastq_set_id}",
    tags=["fastqset query"],
    description="Get a Fastq Set Object by its orcabus id, 'fqs.' prefix is optional"
)
async def get_fastq(
        fastq_set_id: str = Depends(sanitise_fqs_orcabus_id),
        # Include s3 uri - resolve the s3 uri if requested
        include_s3_details: Optional[bool] = Query(
            default=False,
            alias="includeS3Details",
            description="Include the s3 uris for the fastq objects"
        )
) -> FastqSetResponseDict:
    try:
        return FastqSetListResponse(
            fastq_set_list=[
                FastqSetData.get(fastq_set_id)
            ],
            include_s3_details=include_s3_details
        ).model_dump(by_alias=True)[0]
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

# Modified Gets

# GET /fastqSet/{fastqSetId}/toFastqListRows - Get fastq list rows for a given fastq set id
@router.get(
    "/{fastq_set_id}/toFastqListRows",
    tags=["fastqset workflow"],
    description="Return in fastq list row format"
)
async def get_fastq_list_row(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> List[FastqListRowDict]:
    return FastqSetData.get(fastq_set_id).to_fastq_list_rows()

# Patches

# PATCH /fastqSet/{fastqSetId} - Link Fastq add a fastq object to this fastq set
@router.patch(
    "/{fastq_set_id}/linkFastq/{fastq_id}",
    tags=["fastqset update"],
    description="Link a fastq object to this fastq set"
)
async def link_fastq(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id), fastq_id = Depends(sanitise_fqr_orcabus_id)) -> FastqSetResponseDict:
    fastq_set_obj = FastqSetData.get(fastq_set_id)
    fastq_obj = FastqListRowData.get(fastq_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq exists
    if fastq_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq '{fastq_id}' does not exist"
        )

    # Check fastq set is open to additional fastqs
    if not fastq_set_obj.allow_additional_fastq:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set '{fastq_set_id}' does not allow additional fastqs"
        )

    # Check fastq is not already in a fastq set
    if fastq_obj.fastq_set_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq '{fastq_id}' is already in a fastq set"
        )

    # Check fastq is a valid fastq
    if not fastq_obj.is_valid:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq '{fastq_id}' is not a valid fastq"
        )

    # Add the fastq set id to the fastq object
    fastq_obj.fastq_set_id = fastq_set_id

    # Save the fastq object
    fastq_obj.save()

    # Append fastq object to fastq set
    fastq_set_obj.fastq_set_ids.append(fastq_obj.id)
    fastq_set_obj.save()

    # Create dicts (and cache s3 details)
    fastq_set_dict = fastq_set_obj.to_dict()
    fastq_dict = fastq_obj.to_dict()

    # Add in the updated events
    put_fastq_list_row_update_event(
        fastq_list_row_response_object=fastq_dict,
        event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_SET_UPDATED
    )
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_LIST_ROW_LINKED
    )

    return fastq_set_dict


# PATCH /fastqSet/{fastqSetId} - Unlink Fastq remove a fastq object from this fastq set
@router.patch(
    "/{fastq_set_id}/unlinkFastq/{fastq_id}",
    tags=["fastqset update"],
    description="Unlink a fastq object to this fastq set"
)
async def unlink_fastq(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id), fastq_id = Depends(sanitise_fqr_orcabus_id)) -> Union[FastqSetResponse, EmptyDict]:
    fastq_set_obj = FastqSetData.get(fastq_set_id)
    fastq_obj = FastqListRowData.get(fastq_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq exists
    if fastq_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq '{fastq_id}' does not exist"
        )

    # Check fastq id is a member of the fastq set
    if fastq_obj.fastq_set_id != fastq_set_id:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq '{fastq_id}' is not a member of fastq set '{fastq_set_id}'"
        )

    # Clean up
    unlink_with_cleanup(fastq_set_obj, fastq_obj)

    # Reload the fastq set
    try:
        fastq_set_obj = FastqSetData.get(fastq_set_id)
    except DoesNotExist as e:
        return {}

    return fastq_set_obj.to_dict()


# PATCH /fastqSet/{fastqSetId} - Set as current fastq, all other fastq sets in this library must first be set to FALSE for this parameter
@router.patch(
    "/{fastq_set_id}/currentFastqSet",
    tags=["fastqset update"],
    description="Set this fastq set as the current fastq set for this library"
)
async def set_is_current_fastq_set(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> FastqSetResponseDict:
    fastq_set_obj = FastqSetData.get(fastq_set_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq set is not already the current fastq set
    if fastq_set_obj.is_current_fastq_set:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set '{fastq_set_id}' is already the current fastq set"
        )

    # Check if there are other fastq sets in the library
    if len(list(FastqSetData.query(
        A.library_orcabus_id == fastq_set_obj.library_orcabus_id,
        filter_condition=(A.id != fastq_set_id) & (A.is_current_fastq_set == True),
        index="library_orcabus_id-index",
        load_full_item=True
    ))) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Another fastq set in library '{fastq_set_obj.library_orcabus_id}' is already the current fastq set"
        )

    # Set the fastq set as the current fastq set
    fastq_set_obj.is_current_fastq_set = True
    fastq_set_obj.save()

    fastq_set_dict = fastq_set_obj.to_dict()
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_IS_CURRENT
    )

    # Return the fastq set as a dictionary
    return fastq_set_dict


# PATCH /fastqSet/{fastqSetId} - Set current fastq flag to false
@router.patch(
    "/{fastq_set_id}/notCurrentFastqSet",
    tags=["fastqset update"],
    description="Set current fastq set flag to false for this fastq set"
)
async def set_is_not_current_fastq_set(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> FastqSetResponseDict:
    fastq_set_obj = FastqSetData.get(fastq_set_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq set is not already the current fastq set
    if not fastq_set_obj.is_current_fastq_set:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set '{fastq_set_id}' current fastq set flag is already set to false"
        )

    # Set the fastq set as the current fastq set
    fastq_set_obj.is_current_fastq_set = False
    fastq_set_obj.save()

    fastq_set_dict = fastq_set_obj.to_dict()
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_IS_NOT_CURRENT
    )

    # Return the fastq set as a dictionary
    return fastq_set_dict

# PATCH /fastqSet/{fastqSetId} - Allow additional fastqs to this fastq sets, all other fastq sets in this library must first be set to FALSE for this parameter
@router.patch(
    "/{fastq_set_id}/allowAdditionalFastqs",
    tags=["fastqset update"],
    description="Allow additional fastqs to this fastq set"
)
async def set_allow_additional_fastqs(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> FastqSetResponseDict:
    fastq_set_obj = FastqSetData.get(fastq_set_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq set is not already allowing additional fastqs
    if fastq_set_obj.allow_additional_fastq:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set '{fastq_set_id}' already allows additional fastqs"
        )

    # Check if there are other fastq sets in the library
    if len(list(filter(
            lambda fastq_set_iter_: fastq_set_iter_.id != fastq_set_id,
            list(FastqSetData.query(
                A.library_orcabus_id == fastq_set_obj.library_orcabus_id,
                filter_condition=(A.allow_additional_fastq == True),
                index="library_orcabus_id-index",
                load_full_item=True
            ))
    ))) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Another fastq set in library '{fastq_set_obj.library_orcabus_id}' is already accepting additional fastqs"
        )

    # Set the fastq set as the current fastq set
    fastq_set_obj.allow_additional_fastq = True
    fastq_set_obj.save()

    fastq_set_dict = fastq_set_obj.to_dict()
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_ADDITIONAL_FASTQS_ALLOWED,
    )

    # Return the fastq set as a dictionary
    return fastq_set_dict


# PATCH - disallowAdditionalFastqs
@router.patch(
    "/{fastq_set_id}/disallowAdditionalFastqs",
    tags=["fastqset update"],
    description="Disallow additional fastqs to this fastq set"
)
async def set_allow_additional_fastqs_to_false(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> FastqSetResponseDict:
    fastq_set_obj = FastqSetData.get(fastq_set_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Check fastq set is not already allowing additional fastqs
    if not fastq_set_obj.allow_additional_fastq:
        raise HTTPException(
            status_code=409,
            detail=f"Fastq set '{fastq_set_id}' already disallows additional fastqs"
        )

    # Set the fastq set as the current fastq set
    fastq_set_obj.allow_additional_fastq = False
    fastq_set_obj.save()

    fastq_set_dict = fastq_set_obj.to_dict()
    put_fastq_set_update_event(
        fastq_set_response_object=fastq_set_dict,
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_ADDITIONAL_FASTQS_DISALLOWED,
    )

    # Return the fastq set as a dictionary
    return fastq_set_dict


# PATCH /merge - Given multiple fastq set ids, merge these into a single fastq set
@router.patch(
    "/merge",
    tags=["fastqset merge"],
    description="Merge multiple fastq sets into a single fastq set"
)
async def merge_fastq_sets(fastq_set_ids: MergePatch = Depends()) -> FastqSetResponseDict:
    # Check that the fastq set ids are unique
    fastq_set_ids = fastq_set_ids.fastq_set_ids
    if len(list(set(fastq_set_ids))) != len(fastq_set_ids):
        raise HTTPException(
            status_code=409,
            detail="Fastq set ids are not unique"
        )

    # Check that there is more than one fastq set id
    if len(list(fastq_set_ids)) < 2:
        raise HTTPException(
            status_code=409,
            detail="Need at least two fastq set ids to merge"
        )

    # Get all items as objects
    fastq_set_obj_list = list(map(
        lambda fastq_set_id_iter_: FastqSetData.get(fastq_set_id_iter_),
        fastq_set_ids
    ))

    # Check all fastq sets exist
    if None in fastq_set_obj_list:
        raise HTTPException(
            status_code=404,
            detail="One or more fastq sets do not exist"
        )

    # Check that the library orcabus id matches for all the fastq sets
    if len(set(list(map(
        lambda fastq_set_obj: fastq_set_obj.library_orcabus_id,
        fastq_set_obj_list
    )))) > 1:
        raise HTTPException(
            status_code=409,
            detail="Fastq sets do not belong to the same library"
        )

    # Collect all the fastq objects
    fastq_obj_id_list = list(set(list(reduce(
        concat,
        list(map(
            lambda fastq_set_obj_iter_: fastq_set_obj_iter_.fastq_set_ids,
            fastq_set_obj_list
        ))
    ))))
    fastq_obj_list = list(map(
        lambda fastq_obj_id_iter_: FastqListRowData.get(fastq_obj_id_iter_),
        fastq_obj_id_list
    ))

    # is_current_fastq_set set to true if true in any of the existing fastq sets
    is_current_fastq_set = any(list(map(
        lambda fastq_set_obj: fastq_set_obj.is_current_fastq_set,
        fastq_set_obj_list
    )))

    # allow_additional_fastq set to true if true in any of the existing fastq sets
    allow_additional_fastq = any(list(map(
        lambda fastq_set_obj: fastq_set_obj.allow_additional_fastq,
        fastq_set_obj_list
    )))

    fastq_list_row_ids = list(map(
        lambda fastq_obj_iter_: fastq_obj_iter_.id,
        fastq_obj_list
    ))

    # Create the FastqSetData object
    new_fastq_set_data_obj = FastqSetData(
        library=LibraryData(**dict(fastq_obj_list[0].library.model_dump(by_alias=True))),
        allow_additional_fastq=allow_additional_fastq,
        is_current_fastq_set=is_current_fastq_set,
        fastq_set_ids=fastq_list_row_ids
    )
    new_fastq_set_data_obj.save()

    # Delete the old fastq sets
    for fastq_set_obj in fastq_set_obj_list:
        fastq_set_obj.delete()
        put_fastq_set_update_event(
            fastq_set_response_object={
                "fastqSetId": fastq_set_obj.id
            },
            event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_DELETED,
        )

    # For each fastq object, update the fastq set id
    for fastq_obj in fastq_obj_list:
        fastq_obj.fastq_set_id = new_fastq_set_data_obj.id
        fastq_obj.save()
        put_fastq_list_row_update_event(
            fastq_list_row_response_object=fastq_obj.to_dict(),
            event_status=FastqListRowStateChangeStatusEventsEnum.FASTQ_LIST_ROW_SET_UPDATED
        )

    new_fastq_set_data_obj_dict = new_fastq_set_data_obj.to_dict()
    put_fastq_set_update_event(
        fastq_set_response_object={
            "newFastqSetId": new_fastq_set_data_obj.id,
            "oldFastqSetIds": fastq_set_ids,
            "libraryId": new_fastq_set_data_obj.library,
            "fastqListRowIds": fastq_list_row_ids
        },
        event_status=FastqSetStateChangeStatusEventsEnum.FASTQ_SET_MERGED,
    )

    # Return the new fastq set object
    return new_fastq_set_data_obj_dict


# GET /fastqSet/{fastqSetId}:validateNtsmInternal
@router.get(
    "/{fastq_set_id}:validateNtsmInternal",
    tags=["fastqset ntsm"],
    description="Validate all fastq list rows in the ntsm match, run all-by-all on the ntsms in the fastq set"
)
async def validate_ntsm_internal(fastq_set_id: str = Depends(sanitise_fqs_orcabus_id)) -> Dict:
    # Get the fastq set object
    fastq_set_obj = FastqSetData.get(fastq_set_id)

    # Check fastq set exists
    if fastq_set_obj is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id}' does not exist"
        )

    # Get the fastq list rows
    fastq_list_rows = list(map(
        lambda fastq_set_id_iter: FastqListRowData.get(fastq_set_id_iter),
        fastq_set_obj.fastq_set_ids
    ))

    # Check fastq list rows have an ntsm object
    if not all(list(filter(
        lambda fastq_list_row_iter_: fastq_list_row_iter_.ntsm is not None,
        fastq_list_rows
    ))):
        raise HTTPException(
            status_code=409,
            detail="One or more fastq list rows do not have ntsm objects"
        )

    # Run all-by-all on the ntsms
    return run_ntsm_eval(
        fastq_set_obj.id
    )


# GET /fastqSet/{fastqSetId}:validateNtsmExternal/{fastqSetId}
@router.get(
    "/{fastq_set_id_x}:validateNtsmExternal/{fastq_set_id_y}",
    tags=["fastqset ntsm"],
    description="Validate all fastq list rows in the ntsm match, run all-by-all on the ntsms in the fastq set"
)
async def validate_ntsm_external(fastq_set_id_x: str = Depends(sanitise_fqs_orcabus_id_x), fastq_set_id_y = Depends(sanitise_fqs_orcabus_id_y)) -> Dict:
    # Get the fastq set object
    fastq_set_obj_x = FastqSetData.get(fastq_set_id_x)
    fastq_set_obj_y = FastqSetData.get(fastq_set_id_y)

    # Check fastq set exists
    if fastq_set_obj_x is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id_x}' does not exist"
        )

    # Get the fastq list rows
    fastq_list_rows_x = list(map(
        lambda fastq_obj_iter_: FastqListRowData.get(fastq_obj_iter_),
        fastq_set_obj_x.fastq_set_ids
    ))

    # Check fastq list rows have an ntsm object
    if not all(list(filter(
        lambda fastq_list_row_iter_: fastq_list_row_iter_.ntsm is not None,
        fastq_list_rows_x
    ))):
        raise HTTPException(
            status_code=409,
            detail="One or more fastq list rows do not have ntsm objects"
        )

    # Check fastq set exists
    if fastq_set_obj_y is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fastq set '{fastq_set_id_y}' does not exist"
        )

    # Get the fastq list rows
    fastq_list_rows_y = list(map(
        lambda fastq_obj_iter_: FastqListRowData.get(fastq_obj_iter_),
        fastq_set_obj_y.fastq_set_ids
    ))

    # Check fastq list rows have an ntsm object
    if not all(list(filter(
        lambda fastq_list_row_iter_: fastq_list_row_iter_.ntsm is not None,
        fastq_list_rows_y
    ))):
        raise HTTPException(
            status_code=409,
            detail="One or more fastq list rows do not have ntsm objects"
        )

    # Run all-by-all on the ntsms
    return run_ntsm_eval(
        fastq_set_obj_x.id, fastq_set_obj_y.id
    )
