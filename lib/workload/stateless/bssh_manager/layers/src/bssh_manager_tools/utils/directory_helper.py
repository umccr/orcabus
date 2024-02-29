#!/usr/bin/env python3

"""
Handle directory outputs
"""

# Standard libraries
from pathlib import Path
from typing import Dict
import typing
import boto3

# Local libraries
from .globals import (
    ICAV2_CACHE_PROJECT_BCLCONVERT_OUTPUT_SSM_PATH,
    ICAV2_CACHE_PROJECT_ID_SSM_PATH,
    ICAV2_CACHE_PROJECT_CTTSO_OUTPUT_SSM_PATH
)
from .logger import get_logger

# Dev libraries
if typing.TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient


# Set logger
logger = get_logger()


# def get_workflow_session_id_from_ica_event_detail(event_detail: Dict) -> Tuple[str, str, datetime]:
#     """
#     Returns the workflow session id from the event details along with the workflow session creation time
#
#     :param event_detail: Dict
#     {
#       "ica-event": {
#         "correlationId": "4a363c2c-d800-44e7-9f81-da93137d23c1",
#         "timestamp": "2024-01-17T01:47:16.551Z",
#         "eventCode": "ICA_WFS_003",
#         "eventParameters": {
#           "workflowSession": "2549717d-ee16-47c2-b12e-59908b980fd7"
#         },
#         "description": "Workflow session success",
#         "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
#         "payload": {
#           "id": "2549717d-ee16-47c2-b12e-59908b980fd7",
#           "timeCreated": "2024-01-17T00:16:17Z",
#           "ownerId": "0c51d29a-8ffa-38e9-bf18-736330d7c65a",
#           "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
#           "tenantName": "umccr-prod",
#           "userReference": "ws_NovaSeqX-Demo_3664cd",
#           "workflow": {
#             "id": "975875cc-41d3-4992-93af-48cc4a26039b",
#             "code": "ica_workflow_1_2-21",
#             "urn": "urn:ilmn:ica:workflow:975875cc-41d3-4992-93af-48cc4a26039b#ica_workflow_1_2-21",
#             "description": "ICA Workflow v2.21.0",
#             "languageVersion": {
#               "id": "2483549a-1530-4973-bb00-f3f6ccb7e610",
#               "name": "20.10.0",
#               "language": "NEXTFLOW"
#             },
#             "workflowTags": {
#               "technicalTags": []
#             },
#             "analysisStorage": {
#               "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
#               "timeCreated": "2021-11-05T10:28:20Z",
#               "timeModified": "2023-05-31T16:38:26Z",
#               "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
#               "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
#               "tenantName": "ica-cp-admin",
#               "name": "Small",
#               "description": "1.2TB"
#             }
#           },
#           "status": "SUCCEEDED",
#           "startDate": "2024-01-17T00:16:29Z",
#           "endDate": "2024-01-17T01:46:51Z",
#           "summary": "",
#           "tags": {
#             "technicalTags": [
#               "/ilmn-runs/bssh_aps2-sh-prod_3593591/",
#               "20231010_pi1-07_0329_A222N7LTD3",
#               "NovaSeqX-Demo",
#               "3664cd46-7ecb-44c5-b17d-dd442437d61b"
#             ],
#             "userTags": [
#               "/ilmn-runs/bssh_aps2-sh-prod_3593591/"
#             ]
#           }
#         }
#       }
#     }
#     """
#
#     return (
#         event_detail.get("projectId"),
#         event_detail.get("eventParameters").get("workflowSession"),
#         datetime.fromisoformat(event_detail.get("payload").get("timeCreated").replace("Z", "+00:00"))
#     )


# def collect_analysis_from_workflow_session(
#         project_id: str,
#         workflow_session_id: str,
#         workflow_session_creation_time: datetime
# ) -> List[Analysis]:
#     """
#     Collect analysis ids by traversing analysis and filtering by the workflow session id
#
#     We sort by -startDate so that the most recent analysis is first, if the last item in the items list, has an
#     earlier date than the workflow session creation time, then we stop looking for analysis here
#
#     :return:
#     """
#
#     configuration = get_icav2_configuration()
#
#     # Initialise API instance
#     with ApiClient(configuration) as api_client:
#         # Create an instance of the API class
#         api_instance = ProjectAnalysisApi(api_client)
#
#     # List through analyses and find those that have a workflow session id
#     analysis_list: List[Analysis] = []
#     page_offset = 0
#     page_size = 100
#
#     # Iterate through analyses sorted by the most recent,
#     # If we find an analysis that is older than the workflow session creation time, then we stop looking
#     # This is because we know that the workflow session creation time will be older than any analysis it generates
#     while True:
#         try:
#             api_response = api_instance.get_analyses(
#                 project_id=project_id,
#                 sort="startDate desc",
#                 page_offset=str(page_offset),
#                 page_size=str(page_size),
#             )
#         except ApiException as e:
#             logger.error("Exception when calling ProjectAnalysisApi->get_analyses: %s\n" % e)
#             raise ApiException
#
#         analysis_list.extend(
#             list(
#                 filter(
#                     lambda analysis_item: (
#                             analysis_item.workflow_session is not None and
#                             analysis_item.workflow_session.id == workflow_session_id
#                     ),
#                     api_response.items
#                 )
#             )
#         )
#
#         page_offset += page_size
#
#         if (
#             page_offset > api_response.total_item_count or
#                 api_response.items[-1].time_created < workflow_session_creation_time
#         ):
#             break
#
#     return analysis_list


# def find_bclconvert_workflow_from_workflow_session_analysis_list(analysis_list: List[Analysis]) -> Analysis:
#     """
#     For all the analysis that match this workflow session, find those that match the workflow session
#     :param analysis_list:
#     :return:
#     """
#
#     try:
#         return next(
#             filter(
#                 lambda analysis_item: (
#                     str(analysis_item.pipeline.code).lower().startswith("bclconvert")
#                 ),
#                 analysis_list
#             )
#         )
#     except StopIteration:
#         logger.error("Could not find bclconvert workflow id from workflow session analysis list")
#         raise StopIteration


# def get_bclconvert_analysis_id_from_workflow_session_detail(event: Dict):
#     """
#     Get the bclconvert analysis id
#     :param event:
#     :return:
#     """
#
#     # Get the workflow session id
#     project_id, workflow_session_id, workflow_session_creation_time = (
#         get_workflow_session_id_from_ica_event_detail(event)
#     )
#
#     # Get analysis associated with this workflow session
#     analysis_list = collect_analysis_from_workflow_session(
#         project_id,
#         workflow_session_id,
#         workflow_session_creation_time
#     )
#
#     bclconvert_workflow = find_bclconvert_workflow_from_workflow_session_analysis_list(analysis_list)
#
#     return bclconvert_workflow.id


def get_basespace_run_id_from_bssh_json_output(bssh_json_output: Dict) -> int:
    """
    From
    {
      ...
      "Projects": {
        "OutputProject": {
          "Name": "bssh_aps2-sh-prod_3593591"
        }
      }
    }

    To

    3593591
    :param bssh_json_output:
    :return:
    """
    return int(
        bssh_json_output
        .get("Projects")
        .get("OutputProject")
        .get("Name")
        .split("_")[-1]
    )


def get_dest_project_id_from_ssm_parameter() -> str:
    """
    Get the output project ID from SSM parameter store
    :return:
    """
    ssm_client: SSMClient = boto3.client("ssm")
    response = ssm_client.get_parameter(
        Name=ICAV2_CACHE_PROJECT_ID_SSM_PATH,
        WithDecryption=False
    )
    return response.get("Parameter").get("Value")


def get_bclconvert_output_path_from_ssm_parameter() -> str:
    """
    Get the output path for bclconvert run outputs from SSM parameter store
    :return:
    """
    ssm_client: SSMClient = boto3.client("ssm")
    response = ssm_client.get_parameter(
        Name=ICAV2_CACHE_PROJECT_BCLCONVERT_OUTPUT_SSM_PATH,
        WithDecryption=False
    )
    return response.get("Parameter").get("Value")


def get_cttso_output_path_from_ssm_parameter() -> str:
    """
    Get the output path for bclconvert run outputs from SSM parameter store
    :return:
    """
    ssm_client: SSMClient = boto3.client("ssm")
    response = ssm_client.get_parameter(
        Name=ICAV2_CACHE_PROJECT_CTTSO_OUTPUT_SSM_PATH,
        WithDecryption=False
    )
    return response.get("Parameter").get("Value")


def get_year_from_run_id(run_id: str) -> str:
    """
    Convert 220101_A00111_0001_AH2Y7KDSXY to 2022
    :return:
    """
    return f"20{run_id.split('_')[0][0:2]}"


def get_month_from_run_id(run_id: str) -> str:
    """
    Convert 220102_A00111_0001_AH2Y7KDSXY to 01
    :param run_id:
    :return:
    """
    return run_id.split('_')[0][2:4]


def generate_bclconvert_output_folder_path(run_id: str, basespace_run_id: int, portal_run_id: str) -> Path:
    """
    Output is as follows
    # <bclconvert_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id>
    :param run_id:
    :param basespace_run_id:
    :param portal_run_id:

    :return:
    """
    return (
            Path(get_bclconvert_output_path_from_ssm_parameter()) /
            get_year_from_run_id(run_id) /
            run_id /
            str(basespace_run_id) /
            portal_run_id
    )


def get_cttso_run_cache_path_root(run_id: str, basespace_run_id: int, portal_run_id: str) -> Path:
    """
    Gets the path to place the samplesheet.csv file for the ctTSO fastq files
    # This is very nested because we need to have separate directories ids for every library id
    # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> /
    # This is also the place for the samplesheet for this run
    :param run_id:
    :param basespace_run_id:
    :param portal_run_id:

    :return:
    """
    return (
            Path(get_cttso_output_path_from_ssm_parameter()) /
            get_year_from_run_id(run_id) /
            run_id /
            str(basespace_run_id) /
            portal_run_id
    )


def get_cttso_library_run_path(run_id: str, basespace_run_id: int, library_id: str, portal_run_id: str) -> Path:
    """
    Get the path to place the ctTSO fastq files required for a run cache
    # This is very nested because we need to have separate run ids for every library id
    # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> + "_run_cache"
    :return:
    """
    return (
            get_cttso_run_cache_path_root(run_id, basespace_run_id, portal_run_id) /
            (library_id + "_run_cache")
    )


def get_cttso_fastq_cache_path(run_id: str, basespace_run_id: int, library_id: str, portal_run_id: str) -> Path:
    """
    Get the path to place the ctTSO fastq files required for a run cache
    # This is very nested because we need to have separate run ids for every library id
    # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> + "_run_cache" / <library_id>
    :return:
    """
    return (
            get_cttso_library_run_path(run_id, basespace_run_id, library_id, portal_run_id) /
            library_id
    )
