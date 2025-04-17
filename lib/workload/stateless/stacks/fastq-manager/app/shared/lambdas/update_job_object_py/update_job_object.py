#!/usr/bin/env python3

"""
No Fastq endpoint to update job with so instead we have to update the fastq object directly in DynamoDB.
"""

import typing
import boto3
from enum import Enum
from os import environ
from datetime import datetime, timezone

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"


def get_dynamo_client() -> 'DynamoDBClient':
    return boto3.client('dynamodb')


def get_job_table_name() -> str:
    return environ['JOB_TABLE_NAME']


def handler(event, context):
    """
    Add fastq object depending on the input parameters.
    :param event:
    :param context:
    :return:
    """
    # Get the job id
    job_id = event.get("jobId")

    # Update the job status
    job_status = JobStatus(event.get("jobStatus"))

    # Get table env
    get_dynamo_client().update_item(
        TableName=get_job_table_name(),
        Key={
            "id": {"S": job_id}
        },
        UpdateExpression="SET #status = :job_status, end_time = :end_time",
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":job_status": {"S": job_status.value},
            ":end_time": {"S": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")}
        }
    )
