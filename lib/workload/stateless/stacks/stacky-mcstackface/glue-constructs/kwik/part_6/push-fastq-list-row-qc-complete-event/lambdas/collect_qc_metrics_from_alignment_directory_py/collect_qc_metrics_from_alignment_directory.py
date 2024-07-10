#!/usr/bin/env python3

"""
Collect the qc metrics from the alignment directory

For WGS Samples, we need to find the mapping_metrics.csv file ->
Find the number of duplicate marked reads through the metric desctiption "Number of duplicate marked reads",
And take the percentage of the duplicate marked reads

pd.read_csv("PRJ241138.mapping_metrics.csv", header=None, names=["rgid_group", "rgid_index", "description", "value", "pct"]).
query("rgid_group=='MAPPING/ALIGNING SUMMARY' and description=='Number of duplicate marked reads'")['pct'].item()

Then we take the wgs_coverage_metrics file to find the mean coverage of the sample
pd.read_csv("PRJ241138.wgs_coverage_metrics.csv", header=None, names=["rgid_group", "rgid_index", "description", "value", "pct"]).
query("rgid_group=='COVERAGE SUMMARY' and description=='Average alignment coverage over genome'")['value'].item()

For RNA Samples we find the quant_metrics.csv file and take the value for 'Fold coverage of all exons'

# Note value is a string, so we need to convert it to a float
pd.read_csv("MDX240202.quant_metrics.csv", header=None, names=["rgid_group", "rgid_index", "description", "value", "pct"]).query("rgid_group=='RNA QUANTIFICATION STATISTICS' and description=='Fold coverage of all exons'")['value'].item()
'107.91'

"""
# Standard imports
import logging
import typing
from typing import List
import pandas as pd
from io import StringIO
from os import environ
import boto3

# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

# Local imports
from wrapica.enums import DataType
from wrapica.libica_models import (
    ProjectData
)
from wrapica.project_data import (
    list_project_data_non_recursively,
    read_icav2_file_contents_to_string, convert_icav2_uri_to_data_obj
)

# Globals
METRIC_COLUMNS = ["rgid_group", "rgid_index", "description", "value", "pct"]

WGS_COVERAGE_SUMMARY_GROUP_NAME = "COVERAGE SUMMARY"
WGS_COVERAGE_MEAN_COVERAGE_DESCRIPTION = "Average alignment coverage over genome"

WGS_MAPPING_METRICS_GROUP_NAME = "MAPPING/ALIGNING SUMMARY"
WGS_MAPPING_METRICS_DUPLICATE_MARKED_READS_DESCRIPTION = "Number of duplicate marked reads"

RNA_QUANTIFICATION_GROUP_NAME = "RNA QUANTIFICATION STATISTICS"
RNA_QUANTIFICATION_FOLD_COVERAGE_OF_ALL_EXONS_DESCRIPTION = "Fold coverage of all exons"

ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Functions
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def icav2_csv_file_to_pd_dataframe(
        project_id: str,
        data_id: str,
        column_names: List[str]
) -> pd.DataFrame:
    """
    Return a pandas DataFrame from the icav2 csv file

    :param project_id:
    :param data_id:
    :param column_names:
    :return:
    """
    return pd.read_csv(
        StringIO(
            read_icav2_file_contents_to_string(
                project_id=project_id,
                data_id=data_id
            )
        ),
        header=None,
        names=column_names
    )


def get_mean_coverage_from_wgs_coverage_file(
        project_id: str,
        coverage_metrics_data_id: str
) -> float:
    """
    Return the mean coverage from the coverage metrics csv file
    :param project_id:
    :param coverage_metrics_data_id:
    :return:
    """
    return float(
        icav2_csv_file_to_pd_dataframe(
            project_id=project_id,
            data_id=coverage_metrics_data_id,
            column_names=METRIC_COLUMNS
        ).query(
            f"rgid_group=='{WGS_COVERAGE_SUMMARY_GROUP_NAME}' and "
            f"description=='{WGS_COVERAGE_MEAN_COVERAGE_DESCRIPTION}'"
        )['value'].item()
    )


def get_duplicate_marked_reads_pct_from_mapping_file(
        project_id: str,
        mapping_metrics_data_id: str
) -> float:
    """
    Return the percentage of duplicate marked reads from the mapping metrics csv file

    :param project_id:
    :param mapping_metrics_data_id:
    :return:
    """
    return float(
        icav2_csv_file_to_pd_dataframe(
            project_id=project_id,
            data_id=mapping_metrics_data_id,
            column_names=METRIC_COLUMNS
        ).query(
            f"rgid_group=='{WGS_MAPPING_METRICS_GROUP_NAME}' and "
            f"description=='{WGS_MAPPING_METRICS_DUPLICATE_MARKED_READS_DESCRIPTION}'"
        )['pct'].item()
    )


def get_fold_coverage_of_all_exons_from_quant_file(
        project_id: str,
        quant_metrics_data_id: str
) -> float:
    """
    Return the fold coverage of all exons from the quantification metrics csv file

    :param project_id:
    :param quant_metrics_data_id:
    :return:
    """
    return float(
        icav2_csv_file_to_pd_dataframe(
            project_id=project_id,
            data_id=quant_metrics_data_id,
            column_names=METRIC_COLUMNS
        ).query(
            f"rgid_group=='{RNA_QUANTIFICATION_GROUP_NAME}' and "
            f"description=='{RNA_QUANTIFICATION_FOLD_COVERAGE_OF_ALL_EXONS_DESCRIPTION}'"
        )['value'].item()
    )


def handler(event, context):
    """
    Given an alignment directory uri (and a sample type), collect the qc metrics from the alignment directory
    :param event:
    :param context:
    :return:
    """
    # Set the environment vars
    set_icav2_env_vars()

    # Get analysis output
    analysis_output_uri = event['analysis_output_uri']
    sample_type = event['sample_type']

    # Get analysis output uri from the event
    # Get analysis output folder as a ProjectData object
    analysis_project_data_obj: ProjectData = convert_icav2_uri_to_data_obj(analysis_output_uri)

    all_output_files: List[ProjectData] = list_project_data_non_recursively(
        project_id=analysis_project_data_obj.project_id,
        parent_folder_id=analysis_project_data_obj.data.id,
        data_type=DataType.FILE
    )

    if sample_type == 'WGS':
        # Find the mapping metrics file
        try:
            mapping_metrics_data_obj = next(
                filter(
                    lambda project_data_iter: project_data_iter.data.details.name.endswith("mapping_metrics.csv"),
                    all_output_files
                )
            )
        except StopIteration:
            logger.error("Could not find the mapping metrics file")
            raise FileNotFoundError

        # Find the coverage metrics file
        try:
            coverage_metrics_data_obj = next(
                filter(
                    lambda project_data_iter: project_data_iter.data.details.name.endswith("wgs_coverage_metrics.csv"),
                    all_output_files
                )
            )
        except StopIteration:
            logger.error("Could not find the coverage metrics file")
            raise FileNotFoundError

        # Get the mean coverage
        mean_coverage = get_mean_coverage_from_wgs_coverage_file(
            project_id=coverage_metrics_data_obj.project_id,
            coverage_metrics_data_id=coverage_metrics_data_obj.data.id
        )

        # Get the percentage of duplicate marked reads
        pct_duplicate_marked_reads = get_duplicate_marked_reads_pct_from_mapping_file(
            project_id=mapping_metrics_data_obj.project_id,
            mapping_metrics_data_id=mapping_metrics_data_obj.data.id
        )

        return {
            "mean_coverage": mean_coverage,
            "pct_duplicate_marked_reads": pct_duplicate_marked_reads
        }
    else:

        # Find the quant metrics file
        try:
            quant_metrics_data_obj = next(
                filter(
                    lambda project_data_iter: project_data_iter.data.details.name.endswith("quant_metrics.csv"),
                    all_output_files
                )
            )
        except StopIteration:
            logger.error("Could not find the quant metrics file")
            raise FileNotFoundError

        # Get the fold coverage of all exons
        fold_coverage_of_all_exons = get_fold_coverage_of_all_exons_from_quant_file(
            project_id=quant_metrics_data_obj.project_id,
            quant_metrics_data_id=quant_metrics_data_obj.data.id
        )

        return {
            "fold_coverage_of_all_exons": fold_coverage_of_all_exons
        }
