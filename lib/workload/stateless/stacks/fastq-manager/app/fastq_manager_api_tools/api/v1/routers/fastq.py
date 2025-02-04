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
from typing import List, Optional, Dict
from fastapi import Depends, Query
from fastapi.routing import APIRouter, HTTPException
from dyntastic import A, DoesNotExist
from functools import reduce

# Import metadata tools
from metadata_tools import (
    list_libraries_in_subject, get_subject_orcabus_id_from_subject_id,
    list_libraries_in_individual, get_individual_orcabus_id_from_individual_id,
    list_libraries_in_project, get_project_orcabus_id_from_project_id,
    list_libraries_in_sample, get_sample_orcabus_id_from_sample_id, get_library_orcabus_id_from_library_id
)

# Model imports
from ....models import BoolQueryEnum, CWLDict, PresignedUrlModel
from ....models.fastq_list_row import FastqListRowResponse, FastqListRowData, FastqListRowCreate, \
    FastqListRowListResponse
from ....models.fastq_pair import FastqPairStorageObjectPatch, FastqPairStorageObjectData
from ....models.file_compression_info import FileCompressionInfoPatch, FileCompressionInfoData
from ....models.ntsm import NtsmUriUpdate, NtsmUriData
from ....models.qc import QcInformationPatch, QcInformationData
from ....models.read_count_info import ReadCountInfoPatch, ReadCountInfoData
from ....utils import (
    is_orcabus_ulid,
    sanitise_fastq_orcabus_id
)

router = APIRouter()


## Query options
@router.get(
    "", tags=["query"],
    description="""
Get a list of FastqListRow objects.<br>
You must specify any of the following combinations:<br>
<ul> 
    <li>rgid and instrumentRunId (this will get you exactly one response)</li>
    <li>instrumentRunId</li>
    <li>one of [library, sample, subject, individual, project]</li>
    <li>one of [library, sample, subject, individual, project] and instrumentRunId</li>
</ul>    

This means you cannot<br>
<ul>
    <li>Specify rgid without specifying instrumentRunId</li>
    <li>Specify multiple metadata attributes</li>
    <li>Specify zero parameters</li>
</ul>

You may query multiple instrumentRunIds and metadata attributes using the <code>[]</code> syntax.<br> 

For example, to query multiple libraries, use <code>library[]=L12345&library[]=L123456</code>
"""
)
async def list_fastq(
        rgid: Optional[str] = None,
        instrument_run_id: Optional[str] = Query(
            None,
            alias="instrumentRunId",
            description="Instrument Run ID, use <code>[]</code> to specify multiple instrument run ids"
        ),
        instrument_run_id_list: Optional[List[str]] = Query(
            None,
            alias="instrumentRunId[]",
            description=None,
            # Don't include into schema, added in instrument run id description
            include_in_schema=False,
            # Allows [] to be passed in as a list
            strict=False
        ),
        # Metadata query - library
        library: Optional[str] = Query(
            None, alias="library",
            description="Either a library id or library orcabus id, use <code>[]</code> to specify multiple libraries, i.e <code>library[]=L12345&library[]=L123456</code>"
        ),
        library_list: Optional[List[str]] = Query(
            None,
            alias="library[]",
            description=None,
            # Don't include into schema, added in library description
            include_in_schema=False,
            # Allows [] to be passed in as a list
            strict=False
        ),
        # Metadata query - sample
        sample: Optional[str] = Query(
            None,
            alias="sample",
            description="Either a sample id or sample orcabus id, use <code>[]</code> to specify multiple samples, i.e <code>sample[]=PRJ12345&sample[]=PRJ567890</code>"
        ),
        sample_list: Optional[List[str]] = Query(
            None,
            alias="sample[]",
            description=None,
            # Don't include into schema, added in sample description
            include_in_schema=False,
            # Allows [] to be passed in as a list
            strict=False
        ),
        # Metadata query - subject
        subject: Optional[str] = Query(
            None,
            alias="subject",
            description="Either a subject id or subject orcabus id, use <code>[]</code> to specify multiple subjects, i.e <code>subject[]=EXT1234&subject[]=EXT5678</code>"
        ),
        subject_list: Optional[List[str]] = Query(
            None,
            alias="subject[]",
            description=None,
            include_in_schema=False,
            strict=False
        ),
        # Metadata query - individual
        individual: Optional[str] = Query(
            None,
            alias="individual",
            description="Either a individual id or individual orcabus id, use <code>[]</code> to specify multiple individuals, i.e <code>individual[]=SBJ1234&individual[]=SBJ1235</code>"
        ),
        individual_list: Optional[List[str]] = Query(
            None,
            alias="individual[]",
            description=None,
            include_in_schema=False,
            strict=False
        ),
        # Metadata query - project
        project: Optional[str] = Query(
            None,
            alias="project",
            description="Either a project id or project orcabus id, use <code>[]</code> to specify multiple projects, i.e <code>project[]=Control&project[]=CustomStudy</code>"
        ),
        project_list: Optional[List[str]] = Query(
            None,
            alias="project[]",
            description=None,
            include_in_schema=False,
            strict=False
        ),
        # Filter query
        valid: Optional[BoolQueryEnum] = BoolQueryEnum.TRUE,
) -> List[FastqListRowResponse]:
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
    # Simple case
    if library is not None:
        library_list = [library]

    # Check sample list
    if sample is not None:
        sample_list = [sample]
    if sample_list is not None:
        sample_orcabus_ids = list(map(
            lambda library_id_iter_: (
                library_id_iter_ if is_orcabus_ulid(library_id_iter_)
                else get_sample_orcabus_id_from_sample_id(library_id_iter_)
            ),
            sample_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each sample
                # Returns a list of lists
                list(map(
                    lambda sample_orcabus_id_iter_:
                    list_libraries_in_sample(sample_orcabus_id_iter_),
                    sample_orcabus_ids
                ))
            ))
        ))

    # Check subject list
    if subject is not None:
        subject_list = [subject]
    if subject_list is not None:
        subject_orcabus_ids = list(map(
            lambda subject_id_iter_: (
                subject_id_iter_ if is_orcabus_ulid(subject_id_iter_)
                else get_subject_orcabus_id_from_subject_id(subject_id_iter_)
            ),
            subject_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each subject
                list(map(
                    lambda subject_orcabus_id_iter_:
                    list_libraries_in_subject(subject_orcabus_id_iter_),
                    subject_orcabus_ids
                ))
            ))
        ))

    # Check individual list
    if individual is not None:
        individual_list = [individual]
    if individual_list is not None:
        individual_orcabus_ids = list(map(
            lambda individual_id_iter_: (
                individual_id_iter_ if is_orcabus_ulid(individual_id_iter_)
                else get_individual_orcabus_id_from_individual_id(individual_id_iter_)
            ),
            individual_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each individual
                list(map(
                    lambda individual_orcabus_id_iter_:
                    list_libraries_in_individual(individual_orcabus_id_iter_),
                    individual_orcabus_ids
                ))
            ))
        ))

    # Check project list
    if project is not None:
        project_list = [project]
    if project_list is not None:
        project_orcabus_ids = list(map(
            lambda project_id_iter_: (
                project_id_iter_ if is_orcabus_ulid(project_id_iter_)
                else get_project_orcabus_id_from_project_id(project_id_iter_)
            ),
            project_list
        ))
        library_list = list(map(
            # Get orcabus id from all library ids
            lambda library_id_iter_: library_id_iter_['orcabusId'],
            # Flatten list of lists of library objects
            list(reduce(
                concat,
                # Get all libraries in each project
                list(map(
                    lambda project_orcabus_id_iter_:
                    list_libraries_in_project(project_orcabus_id_iter_),
                    project_orcabus_ids
                ))
            ))
        ))

    # Check only one of instrument_run_id_list and instrument_run_id is specified
    if instrument_run_id is not None and instrument_run_id_list is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of instrumentRunId or instrumentRunId[] is allowed"
        )
    if instrument_run_id is not None:
        instrument_run_id_list = [instrument_run_id]

    # Check if all the parameters are None
    if all(map(lambda x: x is None, [
        rgid,
        library_list,
        instrument_run_id_list
    ])):
        raise HTTPException(
            status_code=400,
            detail="At least one of rgid, libraryId or instrumentRunId is required"
        )

    # If not, use index queries for each the fastqs and provide an intersection of the results.
    query_lists = []
    if rgid is not None and instrument_run_id_list is None:
        raise HTTPException(
            status_code=400,
            detail="instrumentRunId is required if rgid is provided"
        )
    if rgid is not None and instrument_run_id_list is not None:
        # NOTE: '+' in a query is a reserved character
        # And represented as a space so we need to replace it
        rgid = rgid.replace(" ", "+")
        query_lists.append(
            list(reduce(
                concat,
                list(map(
                    lambda instrument_run_id_iter_: (
                        list(FastqListRowData.query(
                            A.rgid_ext == f"{rgid}.{instrument_run_id_iter_}",
                            filter_condition=filter_expression,
                            index="rgid_ext-index",
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

    # Get the intersection of the query lists
    if len(query_lists) == 1:
        return FastqListRowListResponse(
            fastq_list_rows=list(map(
                lambda fqlr_iter_: fqlr_iter_.to_dict(),
                query_lists[0]
            ))
        ).model_dump()

    # Else query list is greater than one
    # Bind on the id
    fqr_orcabus_ids = set(map(lambda fqlr_iter_: fqlr_iter_.id, query_lists[0]))
    # For each list reduce to the rgids that match the previous set
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
        ))
    ).model_dump(by_alias=True)


# Get a fastq from orcabus id
@router.get(
    "/{fastq_id}",
    tags=["query"],
    description="Get a Fastq List Row Object by its orcabus id, 'fqm.' prefix is optional"
)
async def get_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    try:
        return FastqListRowData.get(fastq_id).to_dict()
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


# Create a fastq object
@router.post("",
             tags=["create"],
             description="Create a Fastq List Row Object, you will need to make sure that the rgid + instrument run id is unique"
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
        ))) == 0, f"Fastq with rgid.instrumentRunId '{fastq_obj.rgid_ext}' already exists"
    except AssertionError as e:
        # Return a 409 Conflict if the fastq already exists
        raise HTTPException(status_code=409, detail=str(e))

    # Save the fastq
    fastq_obj.save()

    # Return the fastq as a dictionary
    return fastq_obj.to_dict()


# MODIFIED GETS
@router.get(
    "/{fastq_id}/toCwl",
    tags=["workflow"],
    description="Return the fastq list row in CWL Workflow Input Schema Format"
)
async def get_fastq_cwl(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> CWLDict:
    return FastqListRowData.get(fastq_id).to_cwl()


@router.get(
    "/{fastq_id}/presign",
    tags=["download"],
    description="Get a presigned url for the fastq files pair"
)
async def get_presigned_url(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> PresignedUrlModel:
    return FastqListRowData.get(fastq_id).presign_uris()


# PATCHES
@router.patch(
    "/{fastq_id}/addQcStats",
    tags=["update"],
    description="Add QC Stats to a Fastq List Row Object"
)
async def add_qc_stats(fastq_id: str = Depends(sanitise_fastq_orcabus_id), qc_obj: QcInformationPatch = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.qc = QcInformationData(**dict(qc_obj.model_dump(by_alias=True)))
    fastq.save()
    return fastq.to_dict()

@router.patch(
    "/{fastq_id}/addReadCount",
    tags=["update"],
    description="Add Read Count Information to a Fastq List Row Object"
)
async def add_read_count(fastq_id: str = Depends(sanitise_fastq_orcabus_id), read_count_obj: ReadCountInfoPatch = Depends()) -> FastqListRowResponse:
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
    tags=["update"],
    description="Add File Compression Information to a Fastq List Row Object"
)
async def add_file_compression(fastq_id: str = Depends(sanitise_fastq_orcabus_id), file_compression_obj: FileCompressionInfoPatch = Depends()) -> FastqListRowResponse:
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
    tags=["update"],
    description="Add Ntsm Storage Object to a Fastq List Row Object"
)
async def add_ntsm_uri(fastq_id: str = Depends(sanitise_fastq_orcabus_id), ntsm: NtsmUriUpdate = Depends()) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.ntsm = NtsmUriData(**dict(ntsm.model_dump())).ntsm
    fastq.save()
    return fastq.to_dict()


# Validation
@router.patch(
    "/{fastq_id}/validate",
    tags=["validate"],
    description="Validate a Fastq List Row Object"
)
async def validate_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = True
    fastq.save()
    return fastq.to_dict()


@router.patch(
    "/{fastq_id}/invalidate",
    tags=["validate"],
    description="Invalidate a Fastq List Row Object, this is useful if an instrument run has failed"
)
async def invalidate_fastq(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
    fastq = FastqListRowData.get(fastq_id)
    fastq.is_valid = False
    fastq.save()
    return fastq.to_dict()


@router.patch(
    "/{fastq_id}/addFastqPairStorageObject",
    tags=["update"],
    description="Add Fastq Pair Storage Object to a Fastq List Row Object"
)
async def add_fastq_pair_storage_object(fastq_id: str = Depends(sanitise_fastq_orcabus_id), fastq_pair_storage_obj: FastqPairStorageObjectPatch = Depends()) -> FastqListRowResponse:
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
    tags=["update"],
    description="Remove Fastq Pair Storage Object from a Fastq List Row Object"
)
async def remove_fastq_pair_storage_object(fastq_id: str = Depends(sanitise_fastq_orcabus_id)) -> FastqListRowResponse:
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
    tags=["delete"],
    description="Delete a Fastq List Row Object"
)
async def delete_fastq(fastq_id: str) -> Dict[str, str]:
    FastqListRowData.get(fastq_id).delete()
    return {"status": "ok"}
