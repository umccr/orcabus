#!/usr/bin/env python3

"""
Use the update push job api to update the status of a job in the database

We expect either a 'RUNNING' update

{
    "jobId": "string",
    "status": "RUNNING",
}

OR

{
    "jobId": "string",
    "hasError": false,
    "errorMessages": "",
    "status": "SUCCEEDED"
}

OR

{
    "jobId": "string",
    "hasError": true,
    "errorMessages": "string",
    "status": "FAILED"
}

"""

from data_sharing_tools import update_push_job_status_from_steps_execution_id


def handler(event, context):
    """
    Get inputs then use the fastq unarchiving tools layer to update the status of a job in the database
    :param event:
    :param context:
    :return:
    """
    # Get inputs
    packaging_job_id = event.get('packagingJobId')
    status = event.get('status')
    has_error = event.get('hasError', False)
    push_job_execution_arn = event.get('pushJobExecutionArn', None)

    # Get job id by querying the steps execution name in the database

    if not has_error:
        return update_push_job_status_from_steps_execution_id(
            steps_execution_id=push_job_execution_arn,
            job_status=status,
            package_job_id=packaging_job_id
        )
    else:
        error_message = event.get('errorMessages', None)
        update_push_job_status_from_steps_execution_id(
            steps_execution_id=push_job_execution_arn,
            job_status=status,
            error_message=error_message,
            package_job_id=packaging_job_id
        )

# if __name__ == '__main__':
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     # Test the handler
#     event = {
#         "pushJobExecutionArn": "arn:aws:states:ap-southeast-2:843407916570:execution:data-sharing-push-parent-sfn:63e9ded0-a2bb-4f71-8aab-63034cce8454",
#         "hasError": True,
#         "errorMessage": {
#             "Error": "States.QueryEvaluationError",
#             "Cause": "An error occurred while executing the state 'Run S3 Data Push' (entered at the event id #6). The JSONata expression '$states.input.pushLocation' specified for the field 'Arguments/Input/pushLocation' returned nothing (undefined)."
#         },
#         "status": "FAILED"
#     }
#     print(json.dumps(
#         handler(event, None),
#         indent=2
#     ))

# if __name__ == '__main__':
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     # Test the handler
#     event = {
#         "packagingJobId": "pkg.01JQYZBHE6PMVX8C3AJHV04GXV",
#         "pushJobExecutionArn": "arn:aws:states:ap-southeast-2:472057503814:execution:data-sharing-push-parent-sfn:9b6f9e3b-0723-416f-b2fa-981ff442da6f",
#         "hasError": False,
#         "errorMessages": None,
#         "status": "SUCCEEDED"
#       }
#     print(json.dumps(
#         handler(event, None),
#         indent=2
#     ))
