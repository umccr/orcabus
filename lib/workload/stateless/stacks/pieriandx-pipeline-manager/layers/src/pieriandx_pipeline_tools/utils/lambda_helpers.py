#!/usr/bin/env python3

"""
Lambda
"""


import boto3
import typing

if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef


def get_aws_lambda_client() -> 'LambdaClient':
    return boto3.client('lambda')


def run_lambda_function(function_name: str, payload: str) -> str:
    client = get_aws_lambda_client()
    response: InvocationResponseTypeDef = client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=payload
    )
    return response['Payload'].read().decode('utf-8')
