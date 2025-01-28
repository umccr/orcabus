#!/usr/bin/env python3

"""
Routes for the API V1 Fastq endpoint

This is the list of routes available
- GET /fastq  (requires at least one of rgid, library_id or instrument_run_id)
- POST /fastq
- GET /fastq/{fastq_id}
- GET /fastq/{fastq_id}/toCwl
- GET /fastq/{fastq_id}/presign
- PATCH /fastq/{fastq_id}/addQcStats
- PATCH /fastq/{fastq_id}/addReadCount
- PATCH /fastq/{fastq_id}/addFileCompressionInformation
- PATCH /fastq/{fastq_id}/addNtsmUri
- PATCH /fastq/{fastq_id}/invalidate
- PATCH /fastq/{fastq_id}/validate
- PATCH /fastq/{fastq_id}/addFastqPairStorageObject
- PATCH /fastq/{fastq_id}/detachFastqPairStorageObject
- DELETE /fastq/{fastq_id}

"""


# Standard imports
from typing import List, Optional, Union, Dict
from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist

# Model imports
from ....models import BoolQueryEnum, CWLDict, PresignedUrlModel
from ....models.fastq_list_row import FastqListRowResponse, FastqListRowData, FastqListRowCreate
from ....models.fastq_pair import FastqPairStorageObjectUpdate, FastqPairStorageObjectData
from ....models.file_compression_info import FileCompressionInfoPatch
from ....models.ntsm import NtsmUriUpdate, NtsmUriData
from ....models.qc import QcInformationPatch, QcInformationData
from ....models.read_count_info import ReadCountInfoPatch
from ....utils import (
    is_orcabus_ulid, get_library_orcabus_id_from_library_id,
    sanitise_fastq_orcabus_id
)

router = APIRouter()

@router.get("/", tags=["fastq"])
async def list_fastq(
        rgid: Optional[str] = None,
        instrument_run_id: Optional[str] = Query(None, alias="instrumentRunId"),
        library_id: Optional[str] =  Query(None, alias="libraryId"),
        valid: Optional[Union[bool | str]] = True,
) -> List[FastqListRowResponse]:
    valid = BoolQueryEnum(valid)
    # Check boolean parameters
    if valid == BoolQueryEnum.ALL:
        filter_expression = None
    else:
        filter_expression = A.is_valid == valid.value

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [rgid, library_id, instrument_run_id])):
        raise HTTPException(
            status_code=400,
            detail="At least one of rgid, library_id or instrument_run_id is required"
        )

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []
    if rgid is not None and instrument_run_id is None:
        raise HTTPException(
            status_code=400,
            detail="instrument_run_id is required if rgid is provided"
        )
    if rgid is not None and instrument_run_id is not None:
        query_lists.append(
            list(FastqListRowData.query(
                A.rgid_ext == f"{rgid}.{instrument_run_id}",
                filter_condition=filter_expression,
                index="rgid_ext-index",
                load_full_item=True
            ))
        )
    if instrument_run_id is not None:
        query_lists.append(
            list(FastqListRowData.query(
                A.instrument_run_id == instrument_run_id,
                filter_condition=filter_expression,
                index="instrument_run_id-index",
                load_full_item=True
            ))
        )
    if library_id is not None:
        library_orcabus_id = (
            library_id if is_orcabus_ulid(library_id)
            else get_library_orcabus_id_from_library_id(library_id)
        )
        query_lists.append(
            list(FastqListRowData.query(
                A.library_orcabus_id == library_orcabus_id,
                filter_condition=filter_expression,
                index="library_orcabus_id-index",
                load_full_item=True
            ))
        )

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return list(map(
            lambda fqlr_iter_: fqlr_iter_.to_dict(),
            query_lists[0]
        ))

    # Else query list is greater than one
    # Bind on the id
    fqr_orcabus_ids = set(map(lambda fqlr_iter_: fqlr_iter_.id, query_lists[0]))
    # For each list reduce to the rgids that match the previous set
    for query_list in query_lists[1:]:
        fqr_orcabus_ids = fqr_orcabus_ids.intersection(
            set(map(lambda fqlr_iter_: fqlr_iter_.id, query_list))
        )

    # Now we have our fqr_orcabus_ids, we can get the FastqListRow objects
    return list(map(
        lambda fqlr_iter_: fqlr_iter_.to_dict(),
        filter(
            lambda fq_iter_: fq_iter_.id in fqr_orcabus_ids,
            query_lists[0]
        )
    ))


@router.post("/", tags=["fastq"])
async def create_fastq(fastq_obj: FastqListRowCreate) -> FastqListRowResponse:
    # First convert the CreateFastqListRow to a FastqListRow
    fastq_obj = FastqListRowData(**dict(fastq_obj.model_dump(by_alias=True)))

    # # Check if the fastq already exists
    try:
        assert len(list(FastqListRowData.query(
            A.rgid_ext == fastq_obj.rgid_ext,
            index="rgid_ext-index",
            load_full_item=True
        ))) == 0, f"Fastq with rgid.instrumentRunId '{fastq_obj.rgid_ext}' already exists"
    except AssertionError as e:
        # Return a 409 Conflict if the fastq already exists
        raise HTTPException(status_code=409, detail=str(e))

    # Save the fastq
    fastq_obj.save()

    # Return the fastq as a dictionary
    return fastq_obj.to_dict()


@router.get("/{fastq_id}", tags=["fastq"])
async def get_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    try:
        return FastqListRowData.get(fastq_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# MODIFIED GETS
@router.get("/{fastq_id}/toCwl", tags=["fastq"])
async def get_fastq_cwl(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> CWLDict:
    return FastqListRowData.get(fastq_id).to_cwl()


@router.get("/{fastq_id}/presign", tags=["fastq"])
async def get_presigned_url(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> PresignedUrlModel:
    return FastqListRowData.get(fastq_id).presign_uris()


# PATCHES
@router.patch("/{fastq_id}/addQcStats", tags=["fastq"])
async def add_qc_stats(fastq_id: str = Depends(sanitise_fastq_orcabus_id), qc_stats: QcInformationPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.qc = QcInformationData(**dict(qc_stats.model_dump(by_alias=True)))
    fastq.save()
    return fastq.to_dict()

@router.patch("/{fastq_id}/addReadCount", tags=["fastq"])
async def add_qc_stats(fastq_id: str = Depends(sanitise_fastq_orcabus_id), read_count_info: ReadCountInfoPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.read_count = read_count_info.read_count
    fastq.base_count_est = read_count_info.base_count_est
    fastq.save()
    return fastq.to_dict()

@router.patch("/{fastq_id}/addFileCompressionInformation", tags=["fastq"])
async def add_file_compression(fastq_id: str = Depends(sanitise_fastq_orcabus_id), file_compression_info: FileCompressionInfoPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.compression_format = file_compression_info.compression_format
    fastq.gzip_compression_size_in_bytes = file_compression_info.gzip_compression_size_in_bytes
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/addNtsmUri", tags=["fastq"])
async def add_ntsm_uri(fastq_id: str = Depends(sanitise_fastq_orcabus_id), ntsm: NtsmUriUpdate = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.ntsm = NtsmUriData(**dict(ntsm.model_dump())).ntsm
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/invalidate", tags=["fastq"])
async def invalidate_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = False
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/validate", tags=["fastq"])
async def validate_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = True
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/addFastqPairStorageObject", tags=["fastq"])
async def add_fastq_pair_storage_object(fastq_pair_storage_object: FastqPairStorageObjectUpdate, fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    # Check that no fastqPairStorageObject exists for this fastq id
    try:
        assert fastq.files is None, "A FastqPairStorageObject already exists for this fastq, please detach it first"
    except AssertionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    fastq.files = FastqPairStorageObjectData(**dict(fastq_pair_storage_object.model_dump(by_alias=True)))
    fastq.save()
    return fastq.to_dict()


@router.patch("/{fastq_id}/detachFastqPairStorageObject", tags=["fastq"])
async def remove_fastq_pair_storage_object(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
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
async def delete_fastq(fastq_id: str) -> Dict[str, str]:
    FastqListRowData.get(fastq_id).delete()
    return {"status": "ok"}
