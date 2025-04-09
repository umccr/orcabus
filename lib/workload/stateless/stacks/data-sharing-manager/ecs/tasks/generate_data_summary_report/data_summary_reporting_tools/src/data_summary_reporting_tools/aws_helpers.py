# Imports
import typing

import pandas as pd
import boto3
import json

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient


from .globals import (
    DYNAMODB_TABLE_NAME,
    DYNAMODB_INDEX_NAME
)

def get_dynamodb_client() -> "DynamoDBClient":
    return boto3.client('dynamodb')


def get_dynamodb_query_response(
        job_id: str,
        context: str
) -> pd.DataFrame:
    """
        "TableName": "{% $dynamoDbTableName %}",
        "IndexName": "content-index",
        "KeyConditionExpression": "#context = :context",
        "ExpressionAttributeNames": {
          "#context": "context"
        },
        "ExpressionAttributeValues": {
          ":context": {
            "S": "{% context_value %}"
          }
        }
    :param job_id:
    :param context:
    :return:
    """
    last_evaluated_key = None
    items_list = []

    while True:
        dynamodb_query_response = get_dynamodb_client().query(
            **dict(filter(
                lambda kv: kv[1] is not None,
                {
                    "TableName": DYNAMODB_TABLE_NAME,
                    "IndexName": DYNAMODB_INDEX_NAME,
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

    return pd.DataFrame(list(map(
        lambda items_iter_: json.loads(items_iter_['content']['S']),
        items_list
    )))


def get_data_from_dynamodb(job_id: str, context: str) -> pd.DataFrame:
    """
    Given a job id, query the dynamodb table to get all data that belongs to that job id for that given data type,
    where data type is one of:
     * library
     * fastq
     * workflow
     * files
    :param job_id:
    :param context:
    :return:
    """

    # If not library, we grab the metadata anyway since we merge it on the other data types.
    return get_dynamodb_query_response(
        job_id,
        context
    )
