#!/usr/bin/env python3

"""
Get presigend url from the s3 uri fastq manager
"""

from filemanager_tools import get_presigned_url, get_file_object_from_ingest_id


def handler(event, context):
    """
    Get the presigned url from the s3 uri
    :param event:
    :param context:
    :return:
    """

    # Part 1 - Get the s3 uri object
    s3_obj = get_file_object_from_ingest_id(event['s3_ingest_id'])

    # Part 2 - Get the presigned url from the s3 object
    presigned_url = get_presigned_url(s3_obj.s3ObjectId)

    return {
        "presigned_url": presigned_url
    }


# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "s3_ingest_id": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     #
#     # {
#     #     "presigned_url": "https://pipeline-dev-cache-503977275616-ap-southeast-2.s3.ap-southeast-2.amazonaws.com/byob-icav2/development/primary/240424_A01052_0193_BH7JMMDRX5/20240910463b8d5d/Samples/Lane_1/LPRJ240775/LPRJ240775_S1_L001_R1_001.fastq.gz?..."
#     # }
