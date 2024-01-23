#!/usr/bin/env python3

"""
Handle the workflow session object
"""
from pathlib import Path
from typing import Dict

from .globals import ICAV2_CACHE_PROJECT_BCLCONVERT_OUTPUT_SSM_PATH, ICAV2_CACHE_PROJECT_ID_SSM_PATH, \
    ICAV2_CACHE_PROJECT_CTTSO_OUTPUT_SSM_PATH

from mypy_boto3_ssm.client import SSMClient
import boto3


def get_bclconvert_analysis_id_from_workflow_session_detail(event_detail: Dict) -> str:
    """
    :param event_detail: Dict

    {
      "correlationId": "cc85de53-d3d6-4b9b-8b2d-b4a082513adb",
      "timestamp": "2024-01-17T01:43:21.404Z",
      "eventCode": "ICA_EXEC_028",
      "eventParameters": {
        "pipelineExecution": "a154ab78-925a-40d8-8f3e-9c065c4e4acb",
        "analysisPreviousStatus": "INPROGRESS",
        "analysisStatus": "SUCCEEDED"
      },
      "description": "Analysis status changed",
      "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
      "payload": {
        "id": "a154ab78-925a-40d8-8f3e-9c065c4e4acb",
        "timeCreated": "2024-01-17T00:23:17Z",
        "timeModified": "2024-01-17T01:43:18Z",
        "ownerId": "0c51d29a-8ffa-38e9-bf18-736330d7c65a",
        "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
        "tenantName": "umccr-prod",
        "reference": "NovaSeqX-Demo_3664cd_3a7062-BclConvert v4_2_7-0ff58e03-efc1-4e25-bdf5-e3ea835df5dc",
        "userReference": "NovaSeqX-Demo_3664cd_3a7062",
        "pipeline": {
          "id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca",
          "timeCreated": "2023-11-13T22:16:50Z",
          "timeModified": "2023-11-16T22:08:46Z",
          "ownerId": "88de7b1d-bd37-37e8-8d29-6213bd79e976",
          "tenantId": "55cb0a54-efab-4584-85da-dc6a0197d4c4",
          "tenantName": "ilmn-dragen",
          "code": "BclConvert v4_2_7",
          "urn": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7",
          "description": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
          "language": "NEXTFLOW",
          "languageVersion": {
            "id": "b1585d18-f88c-4ca0-8d47-34f6c01eb6f3",
            "name": "22.04.3",
            "language": "NEXTFLOW"
          },
          "pipelineTags": {
            "technicalTags": []
          },
          "analysisStorage": {
            "id": "8bc4695d-5b20-43a8-aea3-181b4bf6f07e",
            "timeCreated": "2023-02-16T21:36:11Z",
            "timeModified": "2023-05-31T16:38:09Z",
            "ownerId": "dda792d4-7e9c-3c5c-8d0b-93f0cdddd701",
            "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
            "tenantName": "ica-cp-admin",
            "name": "XLarge",
            "description": "16TB"
          }
        },
        "workflowSession": {
          "id": "2549717d-ee16-47c2-b12e-59908b980fd7",
          "timeCreated": "2024-01-17T00:16:17Z",
          "ownerId": "0c51d29a-8ffa-38e9-bf18-736330d7c65a",
          "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
          "tenantName": "umccr-prod",
          "userReference": "ws_NovaSeqX-Demo_3664cd",
          "workflow": {
            "id": "975875cc-41d3-4992-93af-48cc4a26039b",
            "code": "ica_workflow_1_2-21",
            "urn": "urn:ilmn:ica:workflow:975875cc-41d3-4992-93af-48cc4a26039b#ica_workflow_1_2-21",
            "description": "ICA Workflow v2.21.0",
            "languageVersion": {
              "id": "2483549a-1530-4973-bb00-f3f6ccb7e610",
              "name": "20.10.0",
              "language": "NEXTFLOW"
            },
            "workflowTags": {
              "technicalTags": []
            },
            "analysisStorage": {
              "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
              "timeCreated": "2021-11-05T10:28:20Z",
              "timeModified": "2023-05-31T16:38:26Z",
              "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
              "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
              "tenantName": "ica-cp-admin",
              "name": "Small",
              "description": "1.2TB"
            }
          },
          "status": "INPROGRESS",
          "startDate": "2024-01-17T00:16:29Z",
          "summary": "",
          "tags": {
            "technicalTags": [
              "/ilmn-runs/bssh_aps2-sh-prod_3593591/",
              "20231010_pi1-07_0329_A222N7LTD3",
              "NovaSeqX-Demo",
              "3664cd46-7ecb-44c5-b17d-dd442437d61b"
            ],
            "userTags": [
              "/ilmn-runs/bssh_aps2-sh-prod_3593591/"
            ]
          }
        },
        "status": "SUCCEEDED",
        "startDate": "2024-01-17T00:23:25Z",
        "endDate": "2024-01-17T01:39:09Z",
        "summary": "",
        "analysisStorage": {
          "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
          "timeCreated": "2021-11-05T10:28:20Z",
          "timeModified": "2023-05-31T16:38:26Z",
          "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
          "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
          "tenantName": "ica-cp-admin",
          "name": "Small",
          "description": "1.2TB"
        },
        "analysisPriority": "MEDIUM",
        "tags": {
          "technicalTags": [
            "RUN_ID",
            "RUN_NAME",
            "UNIQUE_ID"
          ],
          "userTags": [],
          "referenceTags": []
        }
      }
    }
    """

    return event_detail.get("payload").get("id")


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


def get_output_project_id_from_ssm_parameter() -> str:
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


def generate_bclconvert_output_folder_path(run_id: str, basespace_run_id: int) -> Path:
    """
    Output is as follows
    # <bclconvert_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id>
    :param run_id:
    :param basespace_run_id:
    :return:
    """
    return (
            Path(get_bclconvert_output_path_from_ssm_parameter()) /
            get_year_from_run_id(run_id) /
            get_month_from_run_id(run_id) /
            run_id /
            str(basespace_run_id)
    )


def get_cttso_run_cache_path(run_id: str, basespace_run_id: int, library_id: str) -> Path:
    """
    Get the path to place the ctTSO fastq files required for a run cache
    # This is very nested because we need to have separate run ids for every library id
    # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> / <run_id>
    # This is the location we will need to place our samplesheets
    :return:
    """
    return (
            Path(get_cttso_output_path_from_ssm_parameter()) /
            get_year_from_run_id(run_id) /
            get_month_from_run_id(run_id) /
            run_id /
            str(basespace_run_id) /
            library_id /
            run_id
    )


def get_cttso_fastq_cache_path(run_id: str, basespace_run_id: int, library_id: str) -> Path:
    """
    Get the path to place the ctTSO fastq files required for a run cache
    # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> / <run_id> / <library_id>
    :return:
    """
    return (
            get_cttso_run_cache_path(run_id, basespace_run_id, library_id) /
            library_id
    )

