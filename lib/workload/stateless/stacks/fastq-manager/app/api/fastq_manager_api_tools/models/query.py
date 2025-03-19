from typing import Optional, List, Dict

from fastapi import Query, HTTPException

from ..utils import get_libraries_from_metadata_query


class BaseQueryParameters:
    def __init__(self):
        self.validate_query()

    def validate_query(self):
        raise NotImplementedError("Subclasses must implement validate_query")


class LabMetadataQueryParameters(BaseQueryParameters):
    def __init__(
            self,
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
                strict=False,
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
            )
    ):
        self.library = library
        self.library_list = library_list
        self.sample = sample
        self.sample_list = sample_list
        self.subject = subject
        self.subject_list = subject_list
        self.individual = individual
        self.individual_list = individual_list
        self.project = project
        self.project_list = project_list

        # Call the super constructor to validate the query
        super().__init__()

    def validate_query(self):
        # Only one of the attributes can be specified
        # Confirm that only one metadata attribute has been specified
        if len(
                list(filter(
                    lambda x: x is not None, [
                        self.library, self.library_list,
                        self.sample, self.sample_list,
                        self.subject, self.subject_list,
                        self.individual, self.individual_list,
                        self.project, self.project_list
                    ]
                ))
        ) > 1:
            raise HTTPException(
                status_code=400,
                detail="Only one of library, sample, subject, individual or project is allowed"
            )

    def set_library_list_from_query(self):
        self.library_list = get_libraries_from_metadata_query(
            self.library, self.library_list,
            self.sample, self.sample_list,
            self.subject, self.subject_list,
            self.individual, self.individual_list,
            self.project, self.project_list
        )

    def to_params_dict(self) -> Dict[str, str]:
        for attr in [
            "sample_list",
            "subject_list",
            "individual_list",
            "project_list",
            "library_list"
        ]:
            # Mutually exclusive attributes
            value = getattr(self, attr)
            if value is not None:
                if isinstance(value, list):
                    return {
                        f"{attr.replace('_list', '')}[]": ','.join(value)
                    }
        return {}


class InstrumentQueryParameters(BaseQueryParameters):
    def __init__(
            self,
            # Instrument Run Id query
            instrument_run_id: Optional[str] = Query(
                None,
                alias="instrumentRunId",
                description="Instrument Run ID, use <code>[]</code> to specify multiple instrument run ids, i.e <code>instrumentRunId[]=250214_A00130_0357_AH5MCFDSXF&instrumentRunId[]=250131_A01052_0253_AH5FY3DSXF</code>"
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
            # Index query
            index: Optional[str] = Query(
                None,
                description="Sample Index to query the Fastq List Row Object"
            ),
            index_list: Optional[List[str]] = Query(
                None,
                alias="index[]",
                description=None,
                # Don't include into schema, added in index description
                include_in_schema=False,
                # Allows [] to be passed in as a list
                strict=False
            ),
            # Lane query
            lane: Optional[int] = Query(
                None,
                description="Lane number"
            ),
            lane_list: Optional[List[int]] = Query(
                None,
                alias="lane[]",
                description=None,
                # Don't include into schema, added in Lane description
                include_in_schema=False,
                # Allows [] to be passed in as a list
                strict=False
            ),
    ):
        self.instrument_run_id = instrument_run_id
        self.instrument_run_id_list = instrument_run_id_list
        self.index = index
        self.index_list = index_list
        self.lane = lane
        self.lane_list = lane_list

        # Call the super constructor to validate the query
        super().__init__()

    def validate_query(self):
        # Assert that only one of index and index_list is specified

        # Check only one of index and index_list is specified
        if self.index is not None and self.index_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of index or index[] is allowed"
            )
        if self.index is not None:
            self.index_list = [self.index]

        # Check only of lane and lane_list is specified
        if self.lane is not None and self.lane_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of lane or lane[] is allowed"
            )
        if self.lane is not None:
            self.lane_list = [self.lane]

        # Check only one of instrument_run_id_list and instrument_run_id is specified
        if self.instrument_run_id is not None and self.instrument_run_id_list is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Only one of instrumentRunId or instrumentRunId[] is allowed"
            )
        if self.instrument_run_id is not None:
            self.instrument_run_id_list = [self.instrument_run_id]

        # Confirm that self.instrument_run_id_list is not None when index or lane is specified
        if self.instrument_run_id_list is None and (self.index_list is not None or self.lane_list is not None):
            raise HTTPException(
                status_code=400,
                detail="instrumentRunId must be specified when index or lane is specified"
            )

    def to_params_dict(self) -> Dict[str, str]:
        params_dict = {}
        for attr in [
            "index_list",
            "lane_list",
            "instrument_run_id_list"
        ]:
            value = getattr(self, attr)
            if value is not None:
                if isinstance(value, list):
                    params_dict.update({
                        f"{attr.replace('_list', '')}[]": ','.join(value)
                    })

            return params_dict


class FastqSetIdQueryParameters(BaseQueryParameters):
    def __init__(
            self,
            # Fastq Set id query
            # Fastq Set id
            fastq_set_id: Optional[str] = Query(
                None,
                alias="fastqSetId",
                description="Fastq Set ID, use <code>[]</code> to specify multiple fastq set ids, i.e <code>fastqSetId[]=fqs.12345&fastqSetId[]=fqs.67890</code>"
            ),
            fastq_set_id_list: Optional[List[str]] = Query(
                None,
                alias="fastqSetId[]",
                description=None,
                include_in_schema=False,
                strict=False
            )
    ):
        self.fastq_set_id = fastq_set_id
        self.fastq_set_id_list = fastq_set_id_list
        # Call the super constructor to validate the query
        super().__init__()

    def validate_query(self):
        # Assert that only one of fastq_set_id and fastq_set_id_list is specified
        if self.fastq_set_id is not None and self.fastq_set_id_list is not None:
            raise HTTPException(
                status_code=400,
                detail="Only one of fastqSetId or fastqSetId[] is allowed"
            )

        if self.fastq_set_id is not None:
            self.fastq_set_id_list = [self.fastq_set_id]

    def to_params_dict(self) -> Dict[str, str]:
        for attr in [
            "fastq_set_id_list"
        ]:
            value = getattr(self, attr)
            if value is not None:
                return {
                    f"{attr.replace('_list', '')}[]": ','.join(map(str, value))
                }
        return {}
