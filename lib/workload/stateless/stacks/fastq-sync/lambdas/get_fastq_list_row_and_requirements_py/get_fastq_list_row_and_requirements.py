#!/usr/bin/env python3

"""
Given a fastq list row and remaining requirements dict, determine which requirements are met by the object and which ones are not.

Given a dictionary as follows

{
    "fastqListRowId": "fqr.1234",
    "requirements": [
        "activeReadSet",
        "hasQc",
        "hasFingerprint"
    ]
}

We return a dictionary like the following
{
    "fastqListRowId": "fqr.1234",
    "satisfiedRequirements": [
        "activeReadSet",
        "hasQc"
    ],
    "unsatisfiedRequirements": [
        "hasFingerprint"
    ]
}
"""


from fastq_tools import get_fastq
from fastq_sync_tools import check_fastq_list_row_against_requirements_list


def handler(event, context):
    """
    Given a fastq list row and a list of requirements,
    determine which requirements are met by the object and which ones are not.
    :param event:
    :param context:
    :return:
    """
    fastq_obj = get_fastq(event['fastqListRowId'], includeS3Details=True)

    satisfied_requirements, unsatisfied_requirements = check_fastq_list_row_against_requirements_list(fastq_obj, event['requirements'])

    return {
        "fastqListRowObj": fastq_obj,
        "satisfiedRequirements": list(map(lambda req_iter_: req_iter_.value, satisfied_requirements)),
        "unsatisfiedRequirements": list(map(lambda req_iter_: req_iter_.value, unsatisfied_requirements))
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
#                 "fastqListRowId": "fqr.01JQ3BETTR9JPV33S3ZXB18HBN",
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
#     #     "fastqListRowObj": {
#     #         "id": "fqr.01JQ3BETTR9JPV33S3ZXB18HBN",
#     #         "fastqSetId": "fqs.01JQ3BETXHQP3FEENYNFJAD7F1",
#     #         "index": "TCTCTACT+GAACCGCG",
#     #         "lane": 4,
#     #         "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC",
#     #         "library": {
#     #             "orcabusId": "lib.01JBB5Y44ZSWKBXJJFHRHJ94CK",
#     #             "libraryId": "L2401548"
#     #         },
#     #         "platform": "Illumina",
#     #         "center": "UMCCR",
#     #         "date": "2024-10-24T00:00:00",
#     #         "readSet": {
#     #             "r1": {
#     #                 "ingestId": "0195c5fb-8352-7a60-b45f-a93989c559a1",
#     #                 "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_4/L2401548/L2401548_S24_L004_R1_001.fastq.ora",
#     #                 "storageClass": "Standard",
#     #                 "gzipCompressionSizeInBytes": null,
#     #                 "rawMd5sum": null
#     #             },
#     #             "r2": {
#     #                 "ingestId": "0195c5fb-8ab5-7f71-8a7d-23fa5bdf3f2d",
#     #                 "s3Uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20250324abcd1234/Samples/Lane_4/L2401548/L2401548_S24_L004_R2_001.fastq.ora",
#     #                 "storageClass": "Standard",
#     #                 "gzipCompressionSizeInBytes": null,
#     #                 "rawMd5sum": null
#     #             },
#     #             "compressionFormat": "ORA"
#     #         },
#     #         "qc": null,
#     #         "ntsm": null,
#     #         "readCount": 517512667,
#     #         "baseCountEst": 1035025334,
#     #         "isValid": true
#     #     },
#     #     "satisfiedRequirements": [
#     #         "hasActiveReadSet"
#     #     ],
#     #     "unsatisfiedRequirements": [
#     #         "hasQc",
#     #         "hasFingerprint",
#     #         "hasFileCompressionInformation"
#     #     ]
#     # }