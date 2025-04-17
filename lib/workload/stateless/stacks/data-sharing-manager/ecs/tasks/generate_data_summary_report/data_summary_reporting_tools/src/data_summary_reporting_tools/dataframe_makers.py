# Imports
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import pandera as pa
import re
from pandera.typing import DataFrame
import humanfriendly

from .aws_helpers import get_data_from_dynamodb
from .models import (
    LibraryModel,
    MetadataSummaryModel,
    FileWithRelativePathModel,
    FastqFileModel,
    FastqSummaryModel,
    SecondaryFileModel,
    DataTypeEnum
)


def get_library_orcabus_from_series_in_fastq_df(series_iter_):
    return list(map(
        lambda library_object_iter_: library_object_iter_['orcabusId'],
        series_iter_['library']
    ))


def get_library_orcabus_from_series_in_linked_library(series_iter_):
    return list(map(
        lambda linked_library_list_iter_: list(map(
            lambda linked_library_dict_iter_: linked_library_dict_iter_['orcabusId'],
            linked_library_list_iter_
        )),
        series_iter_['libraries']
    ))


def get_portal_run_id_from_file_attribute(series_iter_):
    return list(map(
        lambda file_df_iter: (
            file_df_iter[1]['portalRunId']
            if (
                    file_df_iter[1]['attributes'] is not None and
                    isinstance(file_df_iter, Dict) and
                    'portalRunId' in file_df_iter[1]['attributes']
            ) else (
                re.findall(r"/(\d{8}[0-9a-f]{8})/", file_df_iter[1]['key'])[0]
                if re.findall(r"/(\d{8}[0-9a-f]{8})/", file_df_iter[1]['key'])
                else None
            )
        ),
        series_iter_[['attributes', 'key']].iterrows()
    ))



def get_portal_run_id_from_key(series_iter_):
    return list(map(
        lambda file_key_iter_: (
            re.match(r"/(\d{8}[0-9af]{8})/", file_key_iter_).group(1)
        ),
        series_iter_['key']
    ))


def get_ingest_id_list_from_series_in_fastq_df(series_iter_):
    return list(map(
        lambda readset_series_: list(filter(
            lambda ingest_id_iter_: ingest_id_iter_ is not None,
            [
                readset_series_["r1"]["ingestId"],
                readset_series_.get("r2", {}).get("ingestId", None)
            ]
        )),
        series_iter_['readSet']
    ))


def get_compression_format_from_suffix(suffix: str) -> Optional[str]:
    if suffix == ".gz":
        return "GZIP"
    return "ORA"


def get_library_df(job_id: str) -> DataFrame[LibraryModel]:
    """
    Given the job id, query the dynamodb table to get all libraries in the metadata table that
    map to the job id.

    :return:
    """
    # get metadata from dynamodb
    return get_data_from_dynamodb(
        job_id,
        context="library"
    ).pipe(
        DataFrame[LibraryModel]
    )


@pa.check_types
def get_metadata_summary_df(
        library_df: DataFrame[LibraryModel]
) -> DataFrame[MetadataSummaryModel]:
    return DataFrame[MetadataSummaryModel](
        library_df.apply(
            lambda series_iter_: pd.Series({
                "Library ID": series_iter_["libraryId"],
                "Sample ID": series_iter_["sample"].get("sampleId"),
                "External Sample ID": series_iter_["sample"]["externalSampleId"],
                "Subject ID": series_iter_["subject"]["subjectId"],
                "Individual ID": series_iter_["subject"]["individualSet"][0]["individualId"],
                "Project ID": series_iter_["projectSet"][0]["projectId"],
                "Phenotype": series_iter_["phenotype"],
                "Assay": series_iter_["assay"],
                "Type": series_iter_["type"],
            }),
            axis='columns'
        )
    )


@pa.check_types
def get_fastq_df(
        job_id: str,
        library_df: DataFrame[LibraryModel],
        files_df: DataFrame[FileWithRelativePathModel]
) -> Optional[DataFrame[FastqFileModel]]:
    """
    Given a job id, query the dynamodb table to get all fastqs that map to the job id.
    Then transform the fastq table into a pandas dataframe.
    :return:
    """
    fastq_df = get_data_from_dynamodb(
        job_id,
        context="fastq"
    )

    if fastq_df.shape[0] == 0:
        return None

    # Coerce dtypes for readCount and baseCountEst to be int64
    fastq_df['readCount'] = pd.to_numeric(fastq_df['readCount']).fillna(-1).astype('int64')
    fastq_df['baseCountEst'] = pd.to_numeric(fastq_df['baseCountEst']).fillna(-1).astype('int64')

    # Get the fastqs from the database
    return (
        fastq_df.assign(
            library_orcabus_id=lambda series_iter_: get_library_orcabus_from_series_in_fastq_df(series_iter_),
        ).merge(
            library_df,
            left_on="library_orcabus_id",
            right_on="orcabusId",
        ).drop(
            columns="library_orcabus_id"
        ).assign(
            ingest_id=lambda series_iter_: get_ingest_id_list_from_series_in_fastq_df(series_iter_),
        ).explode(
            'ingest_id'
        ).merge(
            files_df,
            left_on="ingest_id",
            right_on="ingestId",
        ).pipe(
            DataFrame[FastqFileModel]
        )
    )


@pa.check_types
def get_fastq_summary_df(
        fastq_df: DataFrame[FastqFileModel],
) -> DataFrame[FastqSummaryModel]:
    # If Compression Format is None, set to suffix of file name
    fastq_summary_df = fastq_df.apply(
        lambda series_iter_: pd.Series({
            "Library ID": series_iter_["libraryId"],
            "Sample ID": series_iter_["sample"]["sampleId"],
            "External Sample ID": series_iter_["sample"]["externalSampleId"],
            "Subject ID": series_iter_["subject"]["subjectId"],
            "Individual ID": series_iter_["subject"]["individualSet"][0]["individualId"],
            "Project ID": series_iter_["projectSet"][0]["projectId"],
            "File Name": Path(series_iter_["relativePath"]).name,
            "Instrument Run ID": series_iter_["instrumentRunId"],
            "Lane": series_iter_["lane"],
            "Compression Format": series_iter_["readSet"]["compressionFormat"],
            "File Size": humanfriendly.format_size(series_iter_["size"]),
            "Relative Output Path": series_iter_["relativePath"],
            # Additional fields for splitting data frames
            "Assay": series_iter_["assay"],
            "Type": series_iter_["type"],
            ## Workaround until the filemanager is synced for the archive bucket
            'Storage Class': series_iter_['storageClass'] if not series_iter_['bucket'].startswith('archive-') else 'DEEP_ARCHIVE',
        }),
        axis="columns"
    )

    # If Compression Format is None, set to suffix of file name
    fastq_summary_df['Compression Format'] = fastq_summary_df.apply(
        lambda series_iter_: (
            series_iter_['Compression Format']
            if series_iter_['Compression Format'] is not None
            else get_compression_format_from_suffix(Path(series_iter_['Relative Output Path']).suffix)
        ),
        axis='columns'
    )

    return DataFrame[FastqSummaryModel](
        fastq_summary_df
    )


def get_files_df(job_id: str) -> DataFrame[FileWithRelativePathModel]:
    return get_data_from_dynamodb(
        job_id,
        context="file"
    ).pipe(
        DataFrame[FileWithRelativePathModel]
    )


def get_analyses_df(
        job_id: str,
        library_df: DataFrame[LibraryModel],
        files_df: DataFrame[FileWithRelativePathModel]
) -> Optional[DataFrame[SecondaryFileModel]]:
    """
    Given a job id, query the dynamodb table to get all analyses that map to the job id.
    Then transform the analyses table into a pandas dataframe.
    :return:
    """
    workflow_df = get_data_from_dynamodb(
        job_id,
        context="workflow"
    )

    if workflow_df.shape[0] == 0:
        return None

    # Get the analyses from the database
    return (
        workflow_df.assign(
            library_orcabus_id=lambda series_iter_: get_library_orcabus_from_series_in_linked_library(series_iter_)
        ).explode(
            "library_orcabus_id"
        ).merge(
            library_df.rename(
                columns={
                    "orcabusId": "library_orcabus_id"
                }
            ),
            on="library_orcabus_id",
        ).merge(
            files_df.query(
                f"dataType == '{DataTypeEnum.SECONDARY_ANALYSIS.value}'"
            ).assign(
                portal_run_id=lambda series_iter_: get_portal_run_id_from_file_attribute(series_iter_)
            ),
            left_on="portalRunId",
            right_on="portal_run_id"
        ).drop(
            columns=[
                "library_orcabus_id",
                "portal_run_id"
            ]
        ).pipe(
            DataFrame[SecondaryFileModel]
        )
    )
