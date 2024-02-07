#!/usr/bin/env python3

"""
Lambda to determine if a given ICAv2 Copy Job has finished.
# From https://docs.aws.amazon.com/step-functions/latest/apireference/API_DescribeExecution.html
# status
# The current status of the execution.
#
# Type: String
#
# Valid Values: RUNNING | SUCCEEDED | FAILED | TIMED_OUT | ABORTED | PENDING_REDRIVE


The event input is
{
    "execution_arn": "arn:aws:states:us-east-1:123456789012:execution:my-state-machine:my-execution",
}

Returns the status as a boolean
* True if the execution arn has succeeded
* False if the execution arn has failed
* None if the execution arn is still running
{
    "status_bool": True
}

"""

import typing
import boto3  # Pretty sure this is built in to the docker image...

# This way we don't actually need mypy in the requirements
# Because TYPE_CHECKING will be False at runtime
if typing.TYPE_CHECKING:
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_stepfunctions.type_defs import DescribeExecutionOutputTypeDef

SUCCESS_STATES = [
    "SUCCEEDED"
]
TERMINAL_STATES = [
    "TIMED_OUT",
    "FAILED",
    "ABORTED"
]
RUNNING_STATES = [
    "RUNNING",
    "PENDING_REDRIVE"
]


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """

    # Set session
    client: SFNClient = boto3.client('stepfunctions')

    # Return status
    execution_arn: DescribeExecutionOutputTypeDef = client.describe_execution(
        executionArn=event['execution_arn']
    )

    # Get the status
    status = execution_arn.get('status')

    if status in SUCCESS_STATES:
        return {
            "status_bool": True
        }
    elif status in TERMINAL_STATES:
        return {
            "status_bool": False
        }
    elif status in RUNNING_STATES:
        return {
            "status_bool": None
        }
    else:
        raise ValueError(f"Unknown status {status}")

