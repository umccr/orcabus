#!/usr/bin/env python3

# Standard imports
from time import sleep
from functools import reduce
from operator import concat
from dyntastic import Dyntastic, DoesNotExist
from os import environ
from pydantic import Field, BaseModel, model_validator, ConfigDict, computed_field
from typing import Optional, Self, List, Union, ClassVar, TypedDict

# Layer imports
from filemanager_tools import (
    get_s3_objs_from_ingest_ids_map
)

# Local imports
from . import FastqListRowDict, PresignedUrlModel, QueryPaginatedResponse
from .fastq_list_row import FastqListRowData, FastqListRowResponse, FastqListRowCreate, FastqListRowResponseDict
from ..cache import update_cache, S3_INGEST_ID_TO_OBJ_MAP_CACHE
from ..globals import FQS_CONTEXT_PREFIX, EVENT_BUS_NAME_ENV_VAR
from ..utils import (
    get_ulid,
    to_snake, to_camel, get_fastq_set_endpoint_url
)

from .library import LibraryData, LibraryResponse, LibraryCreate, LibraryResponseDict


class FastqSetBase(BaseModel):
    # FastqSet base attributes
    # We have the following attributes:
    library: LibraryData
    # fastq_set: List[FastqListRowData]
    allow_additional_fastq: Optional[bool] = False
    is_current_fastq_set: Optional[bool] = True


class FastqSetOrcabusId(BaseModel):
    # fqr.ABCDEFGHIJKLMNOP
    # BCLConvert Metadata attributes
    id: str = Field(default_factory=lambda: f"{FQS_CONTEXT_PREFIX}.{get_ulid()}")


class FastqListSetWithId(FastqSetBase, FastqSetOrcabusId):
    """
    Order class inheritance this way to ensure that the id field is set first
    """
    pass


class FastqSetResponseDict(TypedDict):
    id: str
    library: LibraryResponseDict
    fastqSet: List[FastqListRowResponseDict]
    allowAdditionalFastq: Optional[bool]
    isCurrentFastqSet: Optional[bool]


class FastqSetResponse(FastqListSetWithId):
    # Identical to the CreateFastqSet model but with the addition of the id field
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=to_camel
    )

    # Manually configure the sub fields with their own model configurations
    library: LibraryResponse

    # Fastq set is a computed field
    fastq_set: List[FastqListRowResponse]

    # Set keys to camel case
    @model_validator(mode='before')
    def convert_keys_to_camel(cls, values):
        return {to_camel(k): v for k, v in values.items()}

    # Set the model_dump method response
    def model_dump(self, **kwargs) -> FastqSetResponseDict:
        # Grab the special kwargs
        include_s3_details = False
        if 'include_s3_details' in kwargs:
            kwargs = kwargs.copy()
            include_s3_details = kwargs.pop('include_s3_details')

        # Recursively serialize the object
        data = super().model_dump(**kwargs)

        # Manually serialize the sub fields
        for field_name in ["library", "fastq_set"]:
            field = getattr(self, field_name)
            if field is None:
                continue
            if field is not None:
                if isinstance(field, list):
                    if field_name == 'fastq_set':
                        data[to_camel(field_name)] = list(map(
                            lambda field_iter_: field_iter_.model_dump(**kwargs, include_s3_details=include_s3_details),
                            field
                        ))
                    else:
                        data[to_camel(field_name)] = list(map(
                            lambda field_iter_: field_iter_.model_dump(**kwargs),
                            field
                        ))
                else:
                    data[to_camel(field_name)] = field.model_dump(**kwargs)

        return data


class FastqSetCreate(FastqSetBase):
    # Set the model configuration
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    # Manually configure the sub fields with their own model configurations
    library: LibraryCreate

    # The fastq set can either be a list of FastqListRowCreate objects or existing fastq list row ids
    fastq_set: List[Union[FastqListRowCreate, str]]


class FastqSetData(FastqListSetWithId, Dyntastic):
    # We don't use aliases, instead we convert all keys to snake case first
    # And then we convert them back to camel case in the to_dict method.
    # This separates out serialization to the database store and serialization to the client
    __table_name__ = environ['DYNAMODB_FASTQ_SET_TABLE_NAME']
    __table_host__ = environ['DYNAMODB_HOST']
    __hash_key__ = "id"

    @model_validator(mode='before')
    def convert_to_snake_case(cls, values):
        # Convert the keys to snake caseZ
        return {to_snake(k): v for k, v in values.items()}


    @classmethod
    def from_response(cls, **kwargs) -> Self:
        response_obj = FastqSetResponse(**kwargs)
        response_dict = dict(**response_obj.model_dump(by_alias=True))
        response_dict['fastqSetIds'] = list(map(
            lambda fastq_set_iter_: fastq_set_iter_.id,
            response_obj.fastq_set
        ))

        _ = response_dict.pop('fastqSet')

        return cls(**response_dict)

    fastq_set_ids: List[str]

    @computed_field
    def library_orcabus_id(self) -> str:
        return self.library.orcabus_id

    def _get_fastq_set_from_ids(self) -> List[FastqListRowResponse]:
        return list(map(
            lambda fastq_set_id_iter_: self._get_fastq_list_row_with_retry(fastq_set_id_iter_),
            self.fastq_set_ids
        ))

    def to_dict(self, include_s3_details: Optional[bool] = False) -> FastqSetResponseDict:
        """
        Alternative serialization path to return objects by camel case
        :return:
        """
        # Generate as a dict
        fastq_set_dict = dict(
            **self.model_dump(
                exclude={"library_orcabus_id"}
            )
        )

        # Generate fastq set data
        fastq_set_dict['fastq_set'] = self._get_fastq_set_from_ids()

        # Remove the fastq set ids
        del fastq_set_dict['fastq_set_ids']

        if include_s3_details and not environ.get(EVENT_BUS_NAME_ENV_VAR) == 'local':
            # Get the s3 objects
            s3_objs = get_s3_objs_from_ingest_ids_map(
                list(filter(
                    # Filter out the ingest ids that are already in the cache
                    lambda ingest_id_iter_: ingest_id_iter_ not in S3_INGEST_ID_TO_OBJ_MAP_CACHE,
                    list(map(
                        # Get the ingest ids from the fastq set
                        lambda read_set_obj_iter_: read_set_obj_iter_['ingestId'],
                        list(filter(
                            # Remove any empty read 2 objects
                            lambda read_set_obj_iter_: read_set_obj_iter_ is not None,
                            # Flatten the list
                            list(reduce(
                                concat,
                                # Collect r1 and r2 read sets from each fastq list row
                                list(map(
                                    lambda fqlr_response_iter_: [
                                        fqlr_response_iter_.get('readSet', {}).get('r1', None),
                                        fqlr_response_iter_.get('readSet', {}).get('r2', None)
                                    ],
                                    fastq_set_dict['fastq_set']
                                ))
                            ))
                        ))
                    ))
                ))
            )

            for s3_obj_iter_ in s3_objs:
                update_cache(s3_obj_iter_['ingestId'], s3_obj_iter_['fileObject'])

        # Return as a response
        return FastqSetResponse(
            **fastq_set_dict
        ).model_dump(
            include_s3_details=include_s3_details,
            by_alias=True
        )

    def to_fastq_list_rows(self) -> List[FastqListRowDict]:
        """
        Return as a CWL input object
        :return:
        """
        return list(map(
            lambda fastq_set_iter_: FastqListRowData(**fastq_set_iter_).to_fastq_list_row(),
            self._get_fastq_set_from_ids()
        ))

    def presign_uris(self) -> List[PresignedUrlModel]:
        # Get all unarchived files
        # Presign the URIs
        return list(map(
            lambda fastq_set_iter_: FastqListRowData(**fastq_set_iter_).presign_uris(),
            self._get_fastq_set_from_ids()
        ))

    def model_dump(self, **kwargs):
        # We need to exclude the fastq_set field from the serialization
        # When we are dumping the object to the database
        return super().model_dump(**kwargs)

    @staticmethod
    def _get_fastq_list_row_with_retry(fastq_list_row_id) -> FastqListRowResponse:
        attempts = 0
        while attempts < 3:
            try:
                return FastqListRowData.get(fastq_list_row_id).to_dict()
            except DoesNotExist as e:
                attempts += 1
                sleep(0.5)
        raise DoesNotExist(f"FastqListRow with id {fastq_list_row_id} does not exist")


class FastqSetListResponse(BaseModel):
    # List response
    fastq_set_list: List[FastqSetData]
    include_s3_details: Optional[bool] = False

    def model_dump(self, **kwargs) -> List[FastqSetResponseDict]:
        if len(self.fastq_set_list) == 0:
            return []

        if not self.include_s3_details:
            return list(map(lambda fastq_set_iter_: fastq_set_iter_.to_dict(), self.fastq_set_list))

        # Collect the s3 ingest ids for the fastq list rows
        all_fastq_list_row_ids = list(reduce(
            concat,
            map(
                lambda fastq_set_iter_: fastq_set_iter_.fastq_set_ids,
                self.fastq_set_list
            )
        ))

        all_fastq_list_rows = list(map(
            lambda fqlr_iter_:
            FastqListRowData.get(fqlr_iter_),
            all_fastq_list_row_ids
        ))

        fastqs_with_readsets = list(filter(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set is not None,
            all_fastq_list_rows
        ))

        r1_ingest_ids = list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set.r1.ingest_id,
            fastqs_with_readsets
        ))

        r2_ingest_ids = list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.read_set.r2.ingest_id,
            list(filter(
                lambda fastq_list_row_iter_: hasattr(fastq_list_row_iter_.read_set, 'r2') and fastq_list_row_iter_.read_set.r2 is not None,
                fastqs_with_readsets
            ))
        ))

        # Get the ntsm ingest ids
        ntsm_ingest_ids = list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_.ntsm.ingest_id,
            list(filter(
                lambda fastq_list_row_iter_: fastq_list_row_iter_.ntsm is not None,
                fastqs_with_readsets
            ))
        ))

        s3_list_dict = get_s3_objs_from_ingest_ids_map(
            list(filter(
                lambda ingest_id_iter_: ingest_id_iter_ not in S3_INGEST_ID_TO_OBJ_MAP_CACHE,
                r1_ingest_ids + r2_ingest_ids + ntsm_ingest_ids
            ))
        )

        # Update the cache with the s3 uris
        for row in s3_list_dict:
            update_cache(row['ingestId'], row['fileObject'])

        # Now re-dump the fastq sets
        return list(map(lambda fastq_set_iter_: fastq_set_iter_.to_dict(include_s3_details=True), self.fastq_set_list))


class FastqSetQueryPaginatedResponse(QueryPaginatedResponse):
    """
    Job Query Response, includes a list of jobs, the total
    """
    url_placeholder: ClassVar[str] = get_fastq_set_endpoint_url()
    results: List[FastqSetResponseDict]

    @classmethod
    def resolve_url_placeholder(cls, **kwargs) -> str:
        # Get the url placeholder
        return cls.url_placeholder