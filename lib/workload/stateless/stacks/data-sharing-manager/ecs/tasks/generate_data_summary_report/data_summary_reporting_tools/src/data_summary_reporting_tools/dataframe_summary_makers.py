# Imports
from pathlib import Path
import pandas as pd
from pandera.typing import DataFrame

from .miscell import get_portal_run_id_path_from_relative_path
from .models import SecondaryFileModel, AnalysisSummaryModel, SecondaryFileSummaryModel, StorageEnum


def get_analyses_summary_df(
        analyses_df: DataFrame[SecondaryFileModel],
) -> DataFrame[AnalysisSummaryModel]:
    """
    Given the secondary file model take a row for each portal run id, populate the metadata from the libraries dictionary
    :param analyses_df:
    :return:
    """
    return DataFrame[AnalysisSummaryModel](
        pd.DataFrame(
            analyses_df.apply(
                lambda series_iter_: pd.Series({
                    "library_id": series_iter_["libraryId"],
                    "sample_id": series_iter_["sample"]['sampleId'],
                    "external_sample_id": series_iter_["sample"]['externalSampleId'],
                    "subject_id": series_iter_["subject"]['subjectId'],
                    "individual_id": series_iter_['subject']['individualSet'][0]['individualId'],
                    "project_id": series_iter_['projectSet'][0]['projectId'],
                    "Workflow Name": series_iter_["workflowName"],
                    "Workflow Version": series_iter_["workflowVersion"],
                    "Portal Run ID": series_iter_["portalRunId"],
                    "Relative Output Path": str(get_portal_run_id_path_from_relative_path(
                        Path(series_iter_["relativePath"]),
                        series_iter_["portalRunId"]
                    )) + "/",
                    "Assay": series_iter_["assay"],
                    "Type": series_iter_["type"],
                }),
                axis="columns"
            )
        ).groupby(
            [
                "Workflow Name",
                "Workflow Version",
                "Portal Run ID",
                "Relative Output Path"
            ]
        ).agg(
            library_id_list_str=pd.NamedAgg(column="library_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            sample_id_list_str=pd.NamedAgg(column="sample_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            external_sample_id_list_str=pd.NamedAgg(column="external_sample_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            subject_id_list_str=pd.NamedAgg(column="subject_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            individual_id_list_str=pd.NamedAgg(column="individual_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            project_id_list_str=pd.NamedAgg(column="project_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            assay_list_str=pd.NamedAgg(column="Assay", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            type_list_str=pd.NamedAgg(column="Type", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
        ).reset_index(
        ).rename(
            columns={
                "library_id_list_str": "Library ID",
                "sample_id_list_str": "Sample ID",
                "external_sample_id_list_str": "External Sample ID",
                "subject_id_list_str": "Subject ID",
                "individual_id_list_str": "Individual ID",
                "project_id_list_str": "Project ID",
                "assay_list_str": "Assay",
                "type_list_str": "Type",
            }
        )
    )


def get_secondary_files_summary_df(
        analyses_df: DataFrame[SecondaryFileModel],
) -> DataFrame[SecondaryFileSummaryModel]:
    """
    Given a job id, query the dynamodb table to get all files from all analyses that map to the job id
    Then transform the analyses table into a pandas dataframe
    :param analyses_df:
    :return:
    """
    return DataFrame[SecondaryFileSummaryModel](
        pd.DataFrame(
            analyses_df.apply(
                lambda series_iter_: pd.Series({
                    "library_id": series_iter_["libraryId"],
                    "sample_id": series_iter_["sample"]['sampleId'],
                    "external_sample_id": series_iter_["sample"]['externalSampleId'],
                    "subject_id": series_iter_["subject"]['subjectId'],
                    "individual_id": series_iter_['subject']['individualSet'][0]['individualId'],
                    "project_id": series_iter_['projectSet'][0]['projectId'],
                    "Workflow Name": series_iter_["workflowName"],
                    "Workflow Version": series_iter_["workflowVersion"],
                    "Portal Run ID": series_iter_["portalRunId"],
                    "Relative Output Path": series_iter_["relativePath"],
                    "Assay": series_iter_["assay"],
                    "Type": series_iter_["type"],
                    ## Workaround until the filemanager is synced for the archive bucket
                    "Storage Class": StorageEnum(series_iter_['storageClass']).name,
                }),
                axis="columns"
            ).groupby(
                [
                    "Workflow Name",
                    "Workflow Version",
                    "Portal Run ID",
                    "Relative Output Path",
                    "Storage Class",
                ]
            ).agg(
                library_id_list_str=pd.NamedAgg(column="library_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                sample_id_list_str=pd.NamedAgg(column="sample_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                external_sample_id_list_str=pd.NamedAgg(column="external_sample_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                subject_id_list_str=pd.NamedAgg(column="subject_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                individual_id_list_str=pd.NamedAgg(column="individual_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                project_id_list_str=pd.NamedAgg(column="project_id", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                assay_list_str=pd.NamedAgg(column="Assay", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
                type_list_str=pd.NamedAgg(column="Type", aggfunc=lambda x: "__".join(sorted(list(set(list(x)))))),
            ).reset_index(
            ).rename(
                columns={
                    "library_id_list_str": "Library ID",
                    "sample_id_list_str": "Sample ID",
                    "external_sample_id_list_str": "External Sample ID",
                    "subject_id_list_str": "Subject ID",
                    "individual_id_list_str": "Individual ID",
                    "project_id_list_str": "Project ID",
                    "assay_list_str": "Assay",
                    "type_list_str": "Type",
                }
            )
        )
    )