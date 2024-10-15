#!/usr/bin/env python

"""
Given the environment variable 'SFN_ARN' which represents the ARN of a Step Function,
this script will check the number of running executions of the Step Function
and return the number of running executions
"""

# Imports
import boto3
import typing
from os import environ

# Mypy type hints
if typing.TYPE_CHECKING:
    from mypy_boto3_stepfunctions import SFNClient

# Constants
MAX_CONCURRENCY_ALLOWED = 5


def get_sfn_client() -> 'SFNClient':
    """
    Get the Step Functions client
    :return: SFNClient
    """
    return boto3.client('stepfunctions')


def list_running_executions(sfn_arn: str) -> int:
    """
    List the number of running executions
    """
    sfn_client = get_sfn_client()
    response = sfn_client.list_executions(
        stateMachineArn=sfn_arn,
        statusFilter='RUNNING'
    )
    return len(response['executions'])



def handler(event, context=None):
    """
    Given the environment variable 'SFN_ARN' which represents the ARN of a Step Function,
    this script will check the number of running executions of the Step Function
    and return the number of running executions
    :param event:
    :param context:
    :return:
    """

    sfn_arn = environ.get('SFN_ARN', None)
    if not sfn_arn:
        raise ValueError('SFN_ARN environment variable is required')

    # Get the number of running executions
    running_executions = list_running_executions(sfn_arn)

    # Check if the number of running executions is
    # less than the maximum concurrency allowed
    if running_executions < MAX_CONCURRENCY_ALLOWED:
        return {
            "run_copy_job_step_bool": True,
        }
    else:
        return {
            "run_copy_job_step_bool": False,
        }


# if __name__ == '__main__':
#     from os import environ
#     import json
#     environ["AWS_PROFILE"] = "umccr-production"
#     environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"
#     environ['SFN_ARN'] = 'arn:aws:states:ap-southeast-2:472057503814:stateMachine:cttsov2Sfn-icav2-copy-files-sfn'
#
#     print(
#         json.dumps(
#             handler({}, None),
#             indent=4
#         )
#     )
#
#     # {
#     #     "run_copy_job_step_bool": true
#     # }
