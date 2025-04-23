#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __get_workflow_run_id_from_portal_run_id_lambda_function_arn__

Get workflow for portal run id

"""
import typing
from io import BytesIO
from textwrap import dedent
from time import sleep
from typing import Dict, List, Optional, Tuple
import boto3
import json
from urllib.parse import urlparse

from data_sharing_tools.utils.models import WorkflowRunModelSlim
from metadata_tools import get_library_orcabus_id_from_library_id
from workflow_tools import (
    get_workflow_run_from_portal_run_id, WorkflowRunNotFoundError,
)

import pandas as pd
import ulid
from os import environ

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_athena import AthenaClient


# Globals
# ATHENA
WORKGROUP_ENV_VAR = 'ATHENA_WORKGROUP_NAME'
DATA_SOURCE_ENV_VAR = 'ATHENA_DATASOURCE_NAME'
DATABASE_ENV_VAR = 'ATHENA_DATABASE_NAME'

WORKFLOW_NAME_CONVERSION_MAP = {
    "tumor-normal": "WGS_TUMOR_NORMAL",
    "oncoanalyser_wgs": "oncoanalyser-wgts-dna",
}


def get_athena_client() -> 'AthenaClient':
    return boto3.client('athena')


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def get_bucket_key_tuple_from_s3_uri(s3_uri: str) -> Tuple[str, str]:
    urlobj = urlparse(s3_uri)

    return urlobj.netloc, urlobj.path.lstrip('/')


def run_athena_sql_query(sql_query: str) -> pd.DataFrame:
    athena_query_execution_id = get_athena_client().start_query_execution(
        QueryString=sql_query,
        QueryExecutionContext={
            "Database": environ[DATABASE_ENV_VAR],
            "Catalog": environ[DATA_SOURCE_ENV_VAR]
        },
        WorkGroup=environ[WORKGROUP_ENV_VAR],
    )['QueryExecutionId']

    while True:
        status = get_athena_client().get_query_execution(
            QueryExecutionId=athena_query_execution_id
        )['QueryExecution']['Status']['State']

        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break

        sleep(5)

    if status in ['FAILED', 'CANCELLED']:
        raise RuntimeError(f"Query failed: {status}")

    # Get the results
    result_location = get_athena_client().get_query_execution(
        QueryExecutionId=athena_query_execution_id
    )['QueryExecution']['ResultConfiguration']['OutputLocation']

    bucket, key = get_bucket_key_tuple_from_s3_uri(result_location)

    return pd.read_csv(
        BytesIO(
            get_s3_client().get_object(
                Bucket=bucket,
                Key=key
            )['Body'].read()
        ),
        dtype={
            "portalRunId": "object"
        }
    )


def get_workflow_run_from_portal_run_id_legacy(portal_run_id: str) -> Optional[List[WorkflowRunModelSlim]]:
    workflow_query = dedent(
        """
        SELECT 
          portal_run_id AS portalRunId,
          workflow_name AS workflowName,
          workflow_version AS workflowVersion,
          array_agg(CONCAT('"', library_id, '"')) AS libraries
        FROM workflow
        WHERE portal_run_id = '{__PORTAL_RUN_ID__}'
        GROUP BY portal_run_id, workflow_name, workflow_version
        """.format(
            __PORTAL_RUN_ID__=portal_run_id
        )
    )

    df = run_athena_sql_query(
        workflow_query,
    )

    # Coerce workflow names
    df['workflowName'] = df['workflowName'].apply(
        lambda workflow_name_iter_: (
            WORKFLOW_NAME_CONVERSION_MAP[workflow_name_iter_]
            if workflow_name_iter_ in WORKFLOW_NAME_CONVERSION_MAP
            else workflow_name_iter_
        ),
    )

    df['orcabusId'] = df['portalRunId'].apply(
        lambda portal_run_id_iter_: (
                "wv1." + str(ulid.from_timestamp(pd.to_datetime(portal_run_id_iter_[:8])))
        )
    )

    df['timestamp'] = df['portalRunId'].apply(
        lambda portal_run_id_iter_: pd.to_datetime(portal_run_id_iter_[:8]).isoformat() + "Z"
    )

    df['libraries'] = df['libraries'].apply(
        lambda library_id_list_iter_: (
            json.loads(library_id_list_iter_)
        )
    )

    df['libraries'] = df['libraries'].apply(
        lambda library_id_list_iter_: list(map(
            lambda library_id_iter_: ({
                "libraryId": library_id_iter_,
                "orcabusId": get_library_orcabus_id_from_library_id(library_id_iter_)
            }),
            library_id_list_iter_
        ))
    )

    df = df[[
        'orcabusId',
        'timestamp',
        'workflowName',
        'workflowVersion',
        'portalRunId',
        'libraries'
    ]]

    if df.shape[0] == 0:
        return None

    return df.to_dict(orient='records')


def get_athena_client() -> 'AthenaClient':
    return boto3.client('athena')


def handler(event, context) -> Dict[str, WorkflowRunModelSlim]:
    """
    Get the portal run id, and return as a workflow object
    :param event:
    :param context:
    :return:
    """
    portal_run_id = event['portalRunId']

    try:
        workflow = get_workflow_run_from_portal_run_id(portal_run_id)
        workflow = WorkflowRunModelSlim(
            orcabusId=workflow["orcabusId"],
            timestamp=workflow['currentState']['timestamp'],
            portalRunId=workflow["portalRunId"],
            workflowName=workflow['workflow']['workflowName'],
            workflowVersion=workflow['workflow']['workflowVersion'],
            libraries=workflow['libraries'],
        )
    except WorkflowRunNotFoundError:
        workflow_list = get_workflow_run_from_portal_run_id_legacy(portal_run_id)
        if workflow_list is None:
            raise WorkflowRunNotFoundError(
                f"Workflow with portal run id {portal_run_id} not found in Athena table"
            )
        workflow = workflow_list[0]


    return {
        'workflowRunObject': workflow
    }


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     # Set envs
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['ATHENA_WORKGROUP_NAME'] = 'orcahouse'
#     environ['ATHENA_DATASOURCE_NAME'] = 'orcavault'
#     environ['ATHENA_DATABASE_NAME'] = 'mart'
#
#     print(json.dumps(
#         handler(
#             {
#                 "portalRunId": "20240420746761e7"
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "workflowRunObject": {
#     #         "orcabusId": "wv1.01HKGKG700SJ3EW38M7RP8K8BR",
#     #         "timestamp": "2024-01-07T00:00:00Z",
#     #         "workflowName": "umccrise",
#     #         "workflowVersion": "2.3.1--1--9344851",
#     #         "portalRunId": "202401075d94d609",
#     #         "libraries": [
#     #             {
#     #                 "libraryId": "L2301517",
#     #                 "orcabusId": "lib.01JBMVJ2EPCW8W051H82JF4MTX"
#     #             },
#     #             {
#     #                 "libraryId": "L2301512",
#     #                 "orcabusId": "lib.01JBMVJ1DQHB5HA6MP7BDYE94K"
#     #             }
#     #         ]
#     #     }
#     # }
