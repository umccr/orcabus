#!/usr/bin/env python3

from typing import List, Dict, Optional, Union

from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist

from ....utils import (
    is_orcabus_ulid, get_library_orcabus_id_from_library_id, convert_body_to_snake_case
)
from ....models import FastqListRow, QcInformation, BoolQueryEnum, FastqPairStorageObject

router = APIRouter()

@router.get("/", tags=["fastq"])
async def list_fastq(
        rgid: Optional[str] = None,
        instrument_run_id: Optional[str] = Query(None, alias="instrumentRunId"),
        library_id: Optional[str] =  Query(None, alias="libraryId"),
        valid: Optional[Union[bool | str]] = True,
) -> List[Dict]:
    valid = BoolQueryEnum(valid)
    # Check boolean parameters
    if valid == BoolQueryEnum.ALL:
        filter_expression = None
    else:
        filter_expression = A.is_valid == valid.value

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [rgid, library_id, instrument_run_id])):
        scan_list = FastqListRow.scan(filter_expression)

        return list(map(
            lambda fqlr_iter_: fqlr_iter_.to_dict(),
            scan_list
        ))

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []
    if rgid is not None and instrument_run_id is None:
        raise HTTPException(
            status_code=400,
            detail="instrument_run_id is required if rgid is provided"
        )
    if rgid is not None and instrument_run_id is not None:
        query_lists.append(
            FastqListRow.query(
                A.rgid_ext == f"{rgid}.{instrument_run_id}",
                filter_condition=filter_expression,
                index="rgid_ext-index",
                load_full_item=True
            )
        )
    if instrument_run_id is not None:
        query_lists.append(
            FastqListRow.query(
                A.instrument_run_id == instrument_run_id,
                filter_condition=filter_expression,
                index="instrument_run_id-index",
                load_full_item=True
            )
        )
    if library_id is not None:
        library_orcabus_id = (
            library_id if is_orcabus_ulid(library_id)
            else get_library_orcabus_id_from_library_id(library_id)
        )
        query_lists.append(
            FastqListRow.query(
                A.library_orcabus_id == library_orcabus_id,
                filter_condition=filter_expression,
                index="library_orcabus_id-index",
                load_full_item=True
            )
        )

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return list(map(
            lambda fqlr_iter_: fqlr_iter_.to_dict(),
            query_lists[0]
        ))
    if len(query_lists) > 1:
        # Bind on the id
        query_results = query_lists[0]
        rgids = set(map(lambda fqlr_iter_: fqlr_iter_.id, query_results))
        # For each list reduce to the rgids that match the previous set
        for query_list in query_lists[1:]:
            rgids = rgids.intersection(set(map(lambda fqlr_iter_: fqlr_iter_.id, query_list)))

        # Now we have our rgids, we can get the FastqListRow objects
        return list(map(
            lambda fqlr_iter_: fqlr_iter_.to_dict(),
            filter(
                lambda fq_iter_: fq_iter_.id in rgids,
                query_results
            )
        ))


@router.post("/", tags=["fastq"])
async def create_fastq(fastq: FastqListRow = Depends(convert_body_to_snake_case)) -> Dict:
    # Search the range key rgid_ext for any existing fastq with the same rgid
    fastq = FastqListRow(**fastq)
    try:
        assert len(list(FastqListRow.query(
            A.rgid_ext == fastq.rgid_ext, index="rgid_ext-index", load_full_item=True
        ))) == 0, f"Fastq with rgid.instrumentRunId '{fastq.rgid}.{fastq.instrument_run_id}' already exists"
    except AssertionError as e:
        # Return a 409 Conflict if the fastq already exists
        raise HTTPException(status_code=409, detail=str(e))
    fastq.save()
    return fastq.to_dict()


@router.get("/{fastq_id}", tags=["fastq"])
async def get_fastq(fastq_id: str):
    try:
        return FastqListRow.get(fastq_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# MODIFIED GETS
@router.get("/{fastq_id}/toCwl", tags=["fastq"])
async def get_fastq_cwl(fastq_id: str):
    return FastqListRow.get(fastq_id).to_cwl()


@router.get("/{fastq_id}/presign", tags=["fastq"])
async def get_presigned_url(fastq_id: str):
    return FastqListRow.get(fastq_id).presign_uris()


# PATCHES
@router.patch("/{fastq_id}/addQcStats", tags=["fastq"])
async def add_qc_stats(fastq_id: str, qc_stats: QcInformation):
    fastq = FastqListRow.get(fastq_id)
    fastq.qc = qc_stats
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/addNtsmUri", tags=["fastq"])
async def add_ntsm_uri(fastq_id: str, ntsm_uri: str):
    fastq = FastqListRow.get(fastq_id)
    fastq.ntsm_uri = ntsm_uri
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/invalidate", tags=["fastq"])
async def invalidate_fastq(fastq_id: str):
    fastq = FastqListRow.get(fastq_id)
    fastq.is_valid = False
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/validate", tags=["fastq"])
async def validate_fastq(fastq_id: str):
    fastq = FastqListRow.get(fastq_id)
    fastq.is_valid = True
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/addFastqPairStorageObject", tags=["fastq"])
async def archive(fastq_id: str, fastq_pair_storage_object: FastqPairStorageObject = Depends(convert_body_to_snake_case)):
    fastq = FastqListRow.get(fastq_id)
    # Check that no fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.files is None, "A FastqPairStorageObject already exists for this fastq, please detach it first"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.files = fastq_pair_storage_object
    fastq.save()
    return fastq.to_dict()

@router.patch("/{fastq_id}/detachFastqPairStorageObject", tags=["fastq"])
async def archive(fastq_id: str):
    fastq = FastqListRow.get(fastq_id)
    # Check that the fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.files is not None, "no FastqPairStorageObject does not exists for this fastq"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.files = None
    fastq.save()
    return fastq.to_dict()

# DELETE
@router.delete("/{fastq_id}", tags=["fastq"])
async def delete_fastq(fastq_id: str):
    FastqListRow.get(fastq_id).delete()
    return {"status": "ok"}




