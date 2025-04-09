#!/usr/bin/env python3

"""
Given a fastq set id and a set of requirements, check if the fastq set id meets the requirements.

We need to get all fastq list rows in the fastq set and from there, check if all fastq list row ids meet all requirements.

An example input is as follows:

{
    "fastqSetId": "fqs.12345",
    "requirements": [
        "activeReadSet",
        "hasQc",
        "hasFingerprint",
        "hasFileCompressionInformation"
    ]
}

An example output is as follows:

{
    "hasAllRequirements": true
}

We assume compression metadata is only required for readsets with ORA compression format

"""
from typing import Dict

from fastq_tools import get_fastq_set
from fastq_sync_tools import check_fastq_set_against_requirements_bool, Requirements


def handler(event, context) -> Dict[str, bool]:
    """
    Check if the fastq set id meets the requirements
    :param event:
    :param context:
    :return:
    """

    # Get the fastq set object
    fastq_set_obj = get_fastq_set(event["fastqSetId"], includeS3Details=True)

    # Get requirements
    requirements = list(map(lambda req_iter_: Requirements(req_iter_), event["requirements"]))

    is_unarchiving_allowed = event.get("isUnarchivingAllowed", False)

    return {
        "hasAllRequirements": check_fastq_set_against_requirements_bool(
            fastq_set_obj, requirements, is_unarchiving_allowed
        )
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['BYOB_BUCKET_PREFIX'] = 's3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/'
#     print(json.dumps(
#         handler(
#             {
#                 "fastqSetId": "fqs.01JQ3BEV01G92NWSWD4S59TSE4",
#                 "requirements": [
#                     "hasActiveReadSet",
#                     "hasQc",
#                     "hasFingerprint",
#                     "hasFileCompressionInformation"
#                 ]
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "hasAllRequirements": false
#     # }