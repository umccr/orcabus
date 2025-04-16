#!/usr/bin/env python3

"""

SFN LAMBDA PLACEHOLDER: __list_portal_run_ids_in_library_lambda_function_arn__

List portal run ids from the library.

We also retrieve the portal run id exclusion list, so we filter out any portal run ids
that are in the exclusion list.
"""

import typing
from io import BytesIO
from os import environ
from textwrap import dedent
from time import sleep
from typing import List, Dict, Tuple
from urllib.parse import urlparse

import pandas as pd

import boto3
import ulid

from data_sharing_tools.utils.models import WorkflowRunModelSlim
from workflow_tools import (
    get_workflows_from_library_id
)

if typing.TYPE_CHECKING:
    from metadata_tools import Library
    from mypy_boto3_athena import AthenaClient
    from mypy_boto3_s3 import S3Client

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


def get_legacy_workflows_from_library_id_legacy(library_id: str) -> List[WorkflowRunModelSlim]:
    workflow_query = dedent(
        """
        SELECT 
            portal_run_id AS portalRunId,
            workflow_name AS workflowName,
            workflow_version AS workflowVersion
        FROM workflow
        WHERE (
            library_id IN ('{__LIBRARY_ID__}')
        )
        """.format(
            __LIBRARY_ID__=library_id
        )
    )

    df = run_athena_sql_query(workflow_query)

    if df.shape[0] == 0:
        return []

    # Coerce workflow names
    df['workflowName'] = df['workflowName'].apply(
        lambda workflow_name_iter_: (
            WORKFLOW_NAME_CONVERSION_MAP[workflow_name_iter_]
            if workflow_name_iter_ in WORKFLOW_NAME_CONVERSION_MAP
            else workflow_name_iter_
        ),
    )

    df['timestamp'] = df['portalRunId'].apply(
        lambda portal_run_id_iter_: pd.to_datetime(portal_run_id_iter_[:8], errors='coerce')
    )

    df = df.dropna(
        how='any',
        subset='timestamp'
    )

    df['orcabusId'] = df['portalRunId'].apply(
        lambda portal_run_id_iter_: (
                "wv1." + str(ulid.from_timestamp(pd.to_datetime(portal_run_id_iter_[:8], errors='coerce')))
        )
    )

    df = df[[
        'orcabusId',
        'timestamp',
        'workflowName',
        'workflowVersion',
        'portalRunId'
    ]]

    return df.to_dict(orient='records')


def handler(event, context) -> Dict[str, List[str]]:
    """
    Given a library object, list the portal run ids in the library
    :param event:
    :param context:
    :return:
    """

    # Get library object
    library: 'Library' = event['libraryObject']
    portal_run_id_exclusion_list: List[str] = event['portalRunIdExclusionList']
    secondary_analyses_type_list: List[str] = event['secondaryAnalysisTypeList']

    # List portal run ids in the library
    workflows_list: List[WorkflowRunModelSlim] = list(map(
        lambda workflow_obj_iter_: {
            "orcabusId": workflow_obj_iter_['orcabusId'],
            "timestamp": workflow_obj_iter_['currentState']['timestamp'],
            "workflowName": workflow_obj_iter_['workflow']['workflowName'],
            "portalRunId": workflow_obj_iter_['portalRunId'],
            "workflowVersion": workflow_obj_iter_['workflow']['workflowVersion'],
        },
        get_workflows_from_library_id(library['libraryId'])
    ))

    # Query the datamart for legacy workflows
    workflows_list.extend(get_legacy_workflows_from_library_id_legacy(library['libraryId']))

    # Run athena query to get legacy workflows in the library

    # Filter workflows not in the secondary analyses list
    workflows_list = list(filter(
        lambda workflow_iter_: workflow_iter_['workflowName'] in secondary_analyses_type_list,
        workflows_list
    ))

    # Filter workflows in the exclusion list
    if portal_run_id_exclusion_list:
        workflows_list = list(filter(
            lambda workflow_iter_: workflow_iter_['portalRunId'] not in portal_run_id_exclusion_list,
            workflows_list
        ))

    # For each workflow type, return the most recent workflow of that type
    workflows_list_filter_duplicates = []
    workflows_list.sort(
        key=lambda workflow_iter_: pd.to_datetime(workflow_iter_['timestamp']).timestamp(),
        reverse=True
    )
    # Get the names of all the workflows in the library workflows list
    workflow_names_in_library_workflows = list(set(list(map(
        lambda workflow_iter_: workflow_iter_['workflowName'],
        workflows_list
    ))))
    # Get only the most recent workflow of each type
    for workflow_name_iter_ in workflow_names_in_library_workflows:
        workflows_list_filter_duplicates.append(
            next(filter(
                lambda workflow_iter_: workflow_iter_['workflowName'] == workflow_name_iter_,
                workflows_list
            ))
        )

    # Return the portal run ids of the most recent workflows
    return {
        'portalRunIdList': list(map(
            lambda workflow_iter_: workflow_iter_['portalRunId'],
            workflows_list_filter_duplicates
        ))
    }


if __name__ == '__main__':
    from os import environ
    import json

    # Set envs
    environ['AWS_PROFILE'] = 'umccr-production'
    environ['AWS_REGION'] = 'ap-southeast-2'
    environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
    environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
    environ['ATHENA_WORKGROUP_NAME'] = 'orcahouse'
    environ['ATHENA_DATASOURCE_NAME'] = 'orcavault'
    environ['ATHENA_DATABASE_NAME'] = 'mart'

    print(json.dumps(
        handler({
            "libraryObject": {
                "orcabusId": "lib.01JBMVXY7WQF29A99MNM71X9B3",
                "projectSet": [
                    {
                        "orcabusId": "prj.01JBMVXFEY2HEBA1MDDBVKKX4Z",
                        "projectId": "BPOP",
                        "name": None,
                        "description": None
                    }
                ],
                "sample": {
                    "orcabusId": "smp.01JBMVXY7JSEFPXMDZBY0ZB5RY",
                    "sampleId": "MDX240117",
                    "externalSampleId": "MAFI030524-G",
                    "source": "blood"
                },
                "subject": {
                    "orcabusId": "sbj.01JBMVXY3R7EMJ73M0TB20E0AM",
                    "individualSet": [
                        {
                            "orcabusId": "idv.01JBMVXY3JHEXZ0K0JHEM632QZ",
                            "individualId": "SBJ04893",
                            "source": "lab"
                        }
                    ],
                    "subjectId": "10083361 GL0196"
                },
                "libraryId": "L2400519",
                "phenotype": "normal",
                "workflow": "clinical",
                "quality": "good",
                "type": "WGS",
                "assay": "TsqNano",
                "coverage": 40,
                "overrideCycles": "Y151;I8;I8;Y151"
            },
            "portalRunIdExclusionList": None,
            "secondaryAnalysisTypeList": [
                "umccrise"
            ]
        },
            context=None,
        ),
        indent=4
    ))

    # {
    #     "portalRunIdList": [
    #         "202401075d94d609"
    #     ]
    # }
