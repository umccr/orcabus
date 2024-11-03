#!/usr/bin/env python3

"""
Check success analysis results

Success if:
1* Errors folder does not exist besides Logs_Intermediates and Results directories
2* If Results/MetricsOutput.tsv
"""

# Standard imports
import json
import typing
from typing import Union
import logging
from pathlib import Path
from os import environ
import boto3

# Wrapica imports
from wrapica.project_data import (
    get_project_data_obj_from_project_id_and_path,
    read_icav2_file_contents_to_string,
    list_project_data_non_recursively,
    convert_uri_to_project_data_obj,
    ProjectData
)
from wrapica.enums import DataType

# Set logger
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger()

if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
    from mypy_boto3_ssm.client import SSMClient


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


# Functions related to this script
def get_metrics_output_tsv(output_obj: ProjectData) -> str:
    """
    Convert the following to a json

    DRAGEN TruSight Oncology 500 ctDNA v2.6.0 Analysis Software - Metrics Output
    For Research Use Only. Not for use in diagnostic procedures.

    [Header]
    Output Date     2024-09-15
    Output Time     02:46:34
    Pipeline Version        2.6.0.22

    [Run QC Metrics]
    Metric (UOM)    LSL Guideline   USL Guideline   Value
    PCT_Q30_R1 (%)  NA      NA      NA
    PCT_Q30_R2 (%)  NA      NA      NA

    [Analysis Status]
            L2401294
    COMPLETED_ALL_STEPS     FALSE
    FAILED_STEPS    DragenCaller
    STEPS_NOT_EXECUTED      CoverageReports,TmbAnnotation,Tmb,CDxAnnotation,Contamination,DnaFusionFiltering

    [DNA Library QC Metrics]
    Metric (UOM)    LSL Guideline   USL Guideline   L2401294
    CONTAMINATION_SCORE (NA)        0       1227    NA

    [DNA Library QC Metrics for Small Variant Calling and TMB]
    Metric (UOM)    LSL Guideline   USL Guideline   L2401294
    MEDIAN_EXON_COVERAGE (count)    1300    NA      NA
    PCT_EXON_1000X (%)      80.0    NA      NA

    [DNA Library QC Metrics for MSI and Fusions]
    Metric (UOM)    LSL Guideline   USL Guideline   L2401294
    MEDIAN_EXON_COVERAGE (count)    1300    NA      NA

    [DNA Library QC Metrics for CNV Calling]
    Metric (UOM)    LSL Guideline   USL Guideline   L2401294
    GENE_SCALED_MAD (count) 0.000   0.059   NA
    MEDIAN_BIN_COUNT_CNV_TARGET (count)     6.0     NA      NA

    [DNA Expanded Metrics]
    Metric (UOM)    LSL Guideline   USL Guideline   L2401294
    TOTAL_PF_READS (count)  NA      NA      NA
    MEAN_FAMILY_SIZE (count)        NA      NA      NA
    MEDIAN_TARGET_COVERAGE (count)  NA      NA      NA
    PCT_CHIMERIC_READS (%)  NA      NA      NA
    PCT_EXON_500X (%)       NA      NA      NA
    PCT_EXON_1500X (%)      NA      NA      NA
    PCT_READ_ENRICHMENT (%) NA      NA      NA
    PCT_USABLE_UMI_READS (%)        NA      NA      NA
    MEAN_TARGET_COVERAGE (count)    NA      NA      NA
    PCT_ALIGNED_READS (%)   NA      NA      NA
    PCT_CONTAMINATION_EST (%)       NA      NA      NA
    PCT_TARGET_0.4X_MEAN (%)        NA      NA      NA
    PCT_TARGET_500X (%)     NA      NA      NA
    PCT_TARGET_1000X (%)    NA      NA      NA
    PCT_TARGET_1500X (%)    NA      NA      NA
    PCT_DUPLEXFAMILIES (%)  NA      NA      NA
    MEDIAN_INSERT_SIZE (bp) NA      NA      NA
    MAX_SOMATIC_AF (NA)     NA      NA      NA
    PCT_SOFT_CLIPPED_BASES (%)      NA      NA      NA
    PCT_Q30_BASES (%)       NA      NA      NA

    [Notes]
    Run Metrics     Run Metrics are not generated and values are reported as NA when starting analysis from FASTQ files.
    DNA Library QC Metrics  DNA library QC Metrics are evaluated using contamination score
    DNA Library QC Metrics for CNV Calling  GENE_SCALED_MAD LSL guideline only applies to real cell free DNA.
    DNA Library QC Metrics for Small Variant Calling and TMB        MEDIAN_EXON_COVERAGE is a Fusion QC Metric.

    :return:
    """

    # Extend projectdata object to the MetricsOutput.tsv
    metrics_output_project_data_obj = get_project_data_obj_from_project_id_and_path(
        project_id=output_obj.project_id,
        data_path=Path(output_obj.data.details.path) / 'Results/MetricsOutput.tsv',
        data_type=DataType.FILE
    )

    # Read the contents of the MetricsOutput.tsv
    metrics_output_tsv = read_icav2_file_contents_to_string(
        metrics_output_project_data_obj.project_id,
        metrics_output_project_data_obj.data.id
    )

    return metrics_output_tsv


def check_failed_steps(output_obj: ProjectData) -> bool:
    """
    Returns True if the analysis has failed steps
    :param output_obj:
    :return:
    """
    metrics_output_tsv_str = get_metrics_output_tsv(output_obj)

    if 'FAILED_STEPS\tNA' in metrics_output_tsv_str:
        return False
    return True


def check_errors_folder(output_obj: ProjectData) -> Union[ProjectData, bool]:
    """
    Returns True if the Errors folder exists
    :param output_obj:
    :return:
    """

    try:
        errors_folder_project_data_obj = get_project_data_obj_from_project_id_and_path(
            project_id=output_obj.project_id,
            data_path=Path(output_obj.data.details.path) / 'errors',
            data_type=DataType.FOLDER
        )
    except NotADirectoryError:
        return False

    return errors_folder_project_data_obj


def get_workflow_step_of_failure(error_folder_obj: ProjectData) -> str:
    """
    Get the first file in the Errors folder that ends with .json

    Read the json file and return the 'step' attribute value

    :param error_folder_obj:
    :return:
    """

    # Get the first file in the Errors folder that ends with .json
    error_json_file = next(
        filter(
            lambda json_file_iter: json_file_iter.data.details.path.endswith('.json'),
            list_project_data_non_recursively(
                project_id=error_folder_obj.project_id,
                parent_folder_id=error_folder_obj.data.id,
            )
        )
    )

    # Read the json file
    error_json_file_contents_dict = json.loads(
        read_icav2_file_contents_to_string(
            error_json_file.project_id,
            error_json_file.data.id
        )
    )

    # Return the 'step' attribute value
    return error_json_file_contents_dict['step']



def handler(event, context):
    """
    Check success analysis results -

    Passes if FAILED_STEPS\tNA in MetricsOutput.tsv and Errors folder does not exist

    :param event:
    :param context:
    :return:
    """
    # Set icav2 environment variables
    set_icav2_env_vars()

    # Get output uri from event
    output_uri = event['output_uri']

    # Convert uri to project data object
    output_obj = convert_uri_to_project_data_obj(output_uri)

    # Check for failed steps in MetricsOutput.tsv
    has_failed_steps = check_failed_steps(output_obj)

    # If failed steps is false, we can return success
    if not has_failed_steps:
        return {
            'success': True,
            'message': 'Analysis completed successfully'
        }

    # If failed steps is true, find the errors folder
    errors_folder = check_errors_folder(output_obj)

    if not errors_folder:
        logger.error("Errors folder not found, but workflow failed")
        raise Exception("Errors folder not found, but workflow failed")

    # Get the workflow step of failure
    errors_folder: ProjectData
    return {
        'success': False,
        'message': f"Workflow failed at '{get_workflow_step_of_failure(errors_folder)}' step"
    }

# Failed workflow
# if __name__ == "__main__":
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-production"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "output_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/20240922130c78be/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "success": false,
#     #     "message": "Workflow failed at 'FastqValidation' step"
#     # }

# # Passing workflow
# if __name__ == "__main__":
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-production"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "output_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202409151d85b3c4/"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "success": true,
#     #     "message": "Analysis completed successfully"
#     # }
