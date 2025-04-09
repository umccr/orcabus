#!/usr/bin/env python

"""
Used to handle job completions from the unarchiving manager.

The unarchiving manager speaks in fastq list row ids but we need fastq set ids as our starting point.

An example input of this may be:

{
    "fastqListRowIds": [
        "fqr.1234",
        "fqr.5678"
    ]
}

While an example output might be

{
    "fastqSetIds": [
        "fqs.1234",
    ]
}

"""

from typing import List, Dict

from fastq_tools import get_fastq, FastqListRow


def handler(event, context) -> Dict[str, List[str]]:
    """
    Get the fastq set id for each fastq object
    :param event:
    :param context:
    :return:
    """

    fastq_objs: List[FastqListRow] = list(map(
        lambda fastq_list_row_id_iter: get_fastq(fastq_list_row_id_iter),
        event["fastqListRowIdList"]
    ))

    fastq_set_ids = list(set(list(map(
        lambda fastq_obj_iter: fastq_obj_iter["fastqSetId"],
        fastq_objs
    ))))

    return {
        "fastqSetIds": fastq_set_ids
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
#                 "fastqListRowIdList": ["fqr.01JQ3BETTR9JPV33S3ZXB18HBN"],
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "fastqSetIds": [
#     #         "fqs.01JQ3BETXHQP3FEENYNFJAD7F1"
#     #     ]
#     # }
