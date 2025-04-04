#!/usr/bin/env python3

"""
Get the fastq list row from the fastq set id
"""
from typing import Dict, List

from fastq_tools import get_fastq_set, FastqSet


def handler(event, context) -> Dict[str, List[str]]:
    fastq_set_obj: FastqSet = get_fastq_set(event['fastqSetId'])

    return {
        "fastqListRowIdList": list(map(
            lambda fastq_list_row_iter_: fastq_list_row_iter_['id'],
            fastq_set_obj['fastqSet']
        ))
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
#                 "fastqSetId": "fqs.01JQ3BETXHQP3FEENYNFJAD7F1",
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "fastqListRowIdList": [
#     #         "fqr.01JQ3BETTR9JPV33S3ZXB18HBN"
#     #     ]
#     # }