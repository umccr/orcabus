#!/usr/bin/env python3

"""
Get presigend url from the s3 uri fastq manager
"""

from filemanager_tools import get_file_object_from_s3_uri


def handler(event, context):
    """
    Get the presigned url from the s3 uri
    :param event:
    :param context:
    :return:
    """

    # Part 1 - Get the s3 uri object
    s3_obj = get_file_object_from_s3_uri(event['s3_uri'])

    # Part 2 - Return the ingest id
    return {
        "s3_ingest_id": s3_obj.ingestId
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
#                     "s3_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240424_A01052_0193_BH7JMMDRX5/20240910463b8d5d/Samples/Lane_1/LPRJ240775/LPRJ240775_S1_L001_R1_001.fastq.gz"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "s3_ingest_id": "0193cdc0-2092-78d1-8d4e-fa5b090fce38"
#     # }


# # DELETED CASE
# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "s3_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/ora-compression/230901_A00130_0271_AHLMCNDMXY/20241122e7a60009/ctDNA_ctTSO/NTC_ctTSO230829_L2301074_S8_L002_R2_001.fastq.ora"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #   "s3_ingest_id": "019386fe-bd45-7a10-8e5c-fd568aa27925"
#     # }

# # DELETED CASE
# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "s3_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/ora-compression/200702_A00130_0137_AH5KMHDSXY/202411220ea47c66/exome_AgSsCRE/TGX140366_L2000194_topup_S7_L001_R2_001.fastq.ora"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #   "s3_ingest_id": "01937d70-5758-73a0-814a-bfd8c9c65073"
#     # }

# # EXISTING FILE
# if __name__ == "__main__":
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "s3_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/240913_A01052_0227_BHV7CYDSXC/20240915d20fd5fc/Samples/Lane_3/L2401287/L2401287_S9_L003_R2_001.fastq.gz"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #   "s3_ingest_id": "01937d70-5758-73a0-814a-bfd8c9c65073"
#     # }