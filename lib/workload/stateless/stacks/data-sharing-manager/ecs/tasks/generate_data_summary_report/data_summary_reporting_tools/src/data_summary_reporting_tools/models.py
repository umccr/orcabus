# Imports
from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict, List, Dict
import pandera as pa


class DataTypeEnum(Enum):
    FASTQ = "fastq"
    SECONDARY_ANALYSIS = "secondaryAnalysis"


class LibraryBase(TypedDict):
    orcabusId: str
    libraryId: str


class StorageEnum(Enum):
    STANDARD = "Standard"
    STANDARD_IA = "StandardIa"
    INTELLIGENT_TIERING = "IntelligentTiering"
    GLACIER_INSTANT_RETRIEVAL = "GlacierIr"
    GLACIER = "Glacier"
    DEEP_ARCHIVE = "DeepArchive"


class FileStorageObject(TypedDict):
    ingestId: str


class ReadDict(FileStorageObject):
    gzipCompressionSizeInBytes: Optional[int]
    rawMd5sum: Optional[str]


class ReadSet(TypedDict):
    r1: ReadDict
    r2: Optional[ReadDict]
    compressionFormat: Optional[str]


class Qc(TypedDict):
    insertSizeEstimate: float
    rawWgsCoverageEstimate: float
    r1Q20Fraction: float
    r2Q20Fraction: float
    r1GcFraction: float
    r2GcFraction: float
    duplicationFractionEstimate: float


class Project(TypedDict):
    orcabusId: str
    projectId: str
    name: Optional[str]
    description: Optional[str]


class Sample(TypedDict):
    orcabusId: str
    sampleId: str
    externalSampleId: str
    source: Optional[str]


class Individual(TypedDict):
    orcabusId: str
    individualId: str
    source: str


class Subject(TypedDict):
    orcabusId: str
    subjectId: str
    individualSet: List[Individual]


class LibraryModel(pa.DataFrameModel):
    libraryId: str = pa.Field(str_startswith="L")
    orcabusId: str = pa.Field(str_startswith="lib.")
    phenotype: str = pa.Field(isin=[
        "tumor", "normal", "negative-control"
    ])
    workflow: str = pa.Field()
    quality: Optional[str] = pa.Field(nullable=True)
    type: str = pa.Field()
    assay: str = pa.Field()
    coverage: float = pa.Field(ge=0, coerce=True)
    overrideCycles: str = pa.Field()
    sample: Sample = pa.Field()
    projectSet: List[Project] = pa.Field()
    subject: Subject = pa.Field()


class FastqModel(LibraryModel):
    id: str = pa.Field(str_startswith="fqr.")
    fastqSetId: Optional[str] = pa.Field(str_startswith="fqs.")
    index: str = pa.Field()
    lane: int = pa.Field(in_range={"min_value": 1, "max_value": 4})
    instrumentRunId: str = pa.Field()
    library: LibraryBase = pa.Field()
    platform: Optional[str] = pa.Field(nullable=True)
    center: Optional[str] = pa.Field(nullable=True)
    date: Optional[datetime] = pa.Field(coerce=True)
    readSet: Optional[ReadSet] = pa.Field()
    qc: Optional[Qc] = pa.Field(nullable=True)
    readCount: Optional[int] = pa.Field(nullable=True)
    baseCountEst: Optional[int] = pa.Field(nullable=True)
    isValid: bool = pa.Field(nullable=True)
    ntsm: Optional[FileStorageObject] = pa.Field(nullable=True)


class StateDetail(TypedDict):
    orcabusId: str
    status: str
    timestamp: str


class Workflow(TypedDict):
    orcabusId: str
    workflowName: str
    workflowVersion: str


class WorkflowRunSlimModel(LibraryModel):
    orcabusId: str
    timestamp: str
    workflowName: str
    workflowVersion: str
    portalRunId: str
    libraries: List[LibraryBase]


class FileWithRelativePathModel(pa.DataFrameModel):
    # Identifier
    s3ObjectId: str

    # Path attributes
    bucket: str
    key: str

    # File attributes
    eTag: str
    eventTime: str
    eventType: str
    ingestId: str
    isCurrentState: bool
    isDeleteMarker: bool
    lastModifiedDate: str
    numberDuplicateEvents: int
    numberReordered: int
    sequencer: Optional[str] = pa.Field(nullable=True)
    size: int
    storageClass: str

    # Attribute attributes
    attributes: Optional[Dict] = pa.Field(nullable=True)

    # Optional attributes
    deletedDate: Optional[str] = pa.Field(nullable=True)
    deletedSequencer: Optional[str] = pa.Field(nullable=True)
    versionId: Optional[str] = pa.Field(nullable=True)
    sha256: Optional[str] = pa.Field(nullable=True)

    # Extra fields for relative path
    dataType: str = pa.Field(
        isin=list(map(
            lambda enum_iter_: enum_iter_.value,
            dict(DataTypeEnum.__members__).values())
        ))
    relativePath: str


class FastqFileModel(FastqModel, FileWithRelativePathModel):
    pass


class SecondaryFileModel(WorkflowRunSlimModel, FileWithRelativePathModel):
    pass


# Output tables
class MetadataSummaryModel(pa.DataFrameModel):
    library_id: str = pa.Field(alias='Library ID')
    sample_id: str = pa.Field(alias='Sample ID')
    external_sample_id: str = pa.Field(alias='External Sample ID')
    subject_id: str = pa.Field(alias='Subject ID')
    individual_id: str = pa.Field(alias='Individual ID')
    project_id: str = pa.Field(alias='Project ID')
    phenotype: str = pa.Field(alias='Phenotype')
    assay: str = pa.Field(alias='Assay')
    type_: str = pa.Field(alias='Type')


class FastqSummaryModel(pa.DataFrameModel):
    library_id: str = pa.Field(alias='Library ID')
    sample_id: str = pa.Field(alias='Sample ID')  # Hidden Column
    external_sample_id: str = pa.Field(alias='External Sample ID')  # Hidden Column
    subject_id: str = pa.Field(alias='Subject ID')  # Hidden Column
    individual_id: str = pa.Field(alias='Individual ID')  # Hidden Column
    project_id: str = pa.Field(alias='Project ID')  # Hidden Column
    file_name: str = pa.Field(alias='File Name')
    instrument_run_id: str = pa.Field(alias='Instrument Run ID')
    lane: int = pa.Field(alias='Lane')
    compression_format: Optional[str] = pa.Field(alias='Compression Format', nullable=True)
    file_size: str = pa.Field(alias='File Size')
    relative_output_path: str = pa.Field(alias='Relative Output Path')
    # Additional fields for splitting data frames
    assay: str = pa.Field(alias='Assay')  # Hidden column
    type_: str = pa.Field(alias='Type')  # Hidden column
    # Additional fields for formatting purposes
    storage_class: str = pa.Field(alias='Storage Class')  # Hidden column


class AnalysisSummaryModel(pa.DataFrameModel):
    library_id: str = pa.Field(alias="Library ID")  # Hidden column
    sample_id: str = pa.Field(alias="Sample ID")  # Hidden column
    external_sample_id: str = pa.Field(alias="External Sample ID")  # Hidden column
    subject_id: str = pa.Field(alias="Subject ID")  # Hidden column
    individual_id: str = pa.Field(alias="Individual ID")  # Hidden column
    project_id: str = pa.Field(alias="Project ID")  # Hidden column
    workflow_name: str = pa.Field(alias='Workflow Name')
    workflow_version: str = pa.Field(alias='Workflow Version')
    portal_run_id: str = pa.Field(alias='Portal Run ID')
    relative_path: str = pa.Field(alias='Relative Output Path')
    # Additional fields for splitting data frames
    assay: str = pa.Field(alias='Assay')  # Hidden column
    type_: str = pa.Field(alias='Type')  # Hidden column


class SecondaryFileSummaryModel(pa.DataFrameModel):
    library_id: str = pa.Field(alias="Library ID")  # Hidden column
    sample_id: str = pa.Field(alias="Sample ID")  # Hidden column
    external_sample_id: str = pa.Field(alias="External Sample ID")  # Hidden column
    subject_id: str = pa.Field(alias="Subject ID")  # Hidden column
    individual_id: str = pa.Field(alias="Individual ID")  # Hidden column
    project_id: str = pa.Field(alias="Project ID")  # Hidden column
    workflow_name: str = pa.Field(alias='Workflow Name')
    workflow_version: str = pa.Field(alias='Workflow Version')
    portal_run_id: str = pa.Field(alias='Portal Run ID')
    relative_path: str = pa.Field(alias='Relative Output Path')
    # Additional fields for splitting data frames
    assay: str = pa.Field(alias='Assay')  # Hidden column
    type_: str = pa.Field(alias='Type')  # Hidden column
    # Additional fields for formatting purposes
    storage_class: str = pa.Field(alias='Storage Class')  # Hidden column