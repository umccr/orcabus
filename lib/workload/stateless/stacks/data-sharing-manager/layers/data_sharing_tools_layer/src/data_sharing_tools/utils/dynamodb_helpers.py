#!/usr/bin/env python3

"""
We can scrape our data from the dynamodb table using the boto3 library.
This allows us to generate a few quick helpful functions for our data.
This includes

- Get metadata in package
- Get fastqs in package
- Get secondary analyses in package

"""
import json
from os import environ
from datetime import datetime

import boto3
from typing import List, Dict, Union, TypedDict, NotRequired
import typing
from .models import FileObjectWithRelativePathTypeDef, FileObjectWithPresignedUrlTypeDef
from .. import DataTypeEnum

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from fastq_tools import FastqListRow
    from metadata_tools import Library
    from workflow_tools import WorkflowRun


class DynamoDbFileObjectWithPresignedUrlTypeDef(TypedDict):
    file_object: FileObjectWithRelativePathTypeDef
    presigned_url: NotRequired[str]
    presigned_expiry: NotRequired[datetime]


def get_dynamodb_client() -> "DynamoDBClient":
    """
    Get a dynamodb client.
    """
    return boto3.client("dynamodb")


def query_dynamodb_table(
        job_id: str,
        context: str,
        collect_presigned_url: bool = False
) -> List[Dict[str, Union[Dict, str]]]:
    """
    Query a dynamodb table for a key value pair.
    """
    last_evaluated_key = None
    items_list = []

    while True:
        dynamodb_query_response = get_dynamodb_client().query(
            **dict(filter(
                lambda kv: kv[1] is not None,
                {
                    "TableName": environ['PACKAGING_TABLE_NAME'],
                    "IndexName": environ['CONTENT_INDEX_NAME'],
                    "KeyConditionExpression": "#context = :context",
                    "ExpressionAttributeNames": {
                        "#context": "context"
                    },
                    "ExpressionAttributeValues": {
                        ":context": {
                            "S": job_id + "__" + context
                        }
                    },
                    "ExclusiveStartKey": last_evaluated_key
                }.items()
            ))
        )

        # Append the query response
        items_list.extend(dynamodb_query_response['Items'])

        if 'LastEvaluatedKey' in dynamodb_query_response:
            last_evaluated_key = dynamodb_query_response['LastEvaluatedKey']
        else:
            break

    # To determine if this is a primary or secondary data file

    if not collect_presigned_url:
        return list(map(
            lambda item_iter_: json.loads(item_iter_['content']['S']),
            items_list
        ))
    else:
        return list(map(
            lambda item_iter_: {
                "presigned_url": item_iter_.get("presigned_url", {}).get("S", None),
                "presigned_expiry": item_iter_.get("presigned_expiry", {}).get("S", None),
                "file_object": json.loads(item_iter_['content']['S'])
            },
            items_list
        ))


def get_file_objects_with_presigned_urls(
        job_id: str,
) -> List[FileObjectWithPresignedUrlTypeDef]:
    """
    Get the file objects as presigned urls.
    First we collect all other items, fastqs, secondary_analyses
    :param job_id:
    :param file_objects:
    :return:
    """
    # Get the file objects with presigned url
    dynamodb_file_objects_list: List[DynamoDbFileObjectWithPresignedUrlTypeDef] = (
        query_dynamodb_table(job_id, "file", collect_presigned_url=True)
    )

    return list(map(
        lambda item_iter_: dict(
            **item_iter_['file_object'],
            **{
                "presignedUrl": item_iter_.get("presigned_url", None),
            }
        ),
        dynamodb_file_objects_list
    ))