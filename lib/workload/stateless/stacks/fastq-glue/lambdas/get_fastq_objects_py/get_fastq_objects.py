#!/usr/bin/env python3

"""
Get the fastq objects from the library list for a given instruemnt run id
"""


from fastq_tools import get_fastqs_in_libraries_and_instrument_run_id


def handler(event, context):
    """
    Get the fastq objects from the library list for a given instruemnt run id
    :param event:
    :param context:
    :return:
    """

    # Get inputs
    library_id_list = event["libraryIdList"]
    instrument_run_id = event["instrumentRunId"]

    # Get the fastq objects
    fastq_objects = get_fastqs_in_libraries_and_instrument_run_id(library_id_list, instrument_run_id)

    # Return the fastq objects split by library
    return {
        "fastqIdsByLibrary": list(map(
            lambda library_id_iter_: {
                "libraryId": library_id_iter_,
                "fastqIdList": list(map(
                    lambda fastq_object_iter_: fastq_object_iter_["id"],
                    list(filter(
                        lambda fastq_object_iter_: fastq_object_iter_["library"]["libraryId"] == library_id_iter_,
                        fastq_objects
                    ))
                ))
            },
            library_id_list
        ))
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(json.dumps(
#         handler(
#             {
#                 "instrumentRunId": "250307_A00130_0360_BHCLW2DSXF",
#                 "libraryIdList": [
#                     "L2500185",
#                     "L2500181",
#                     "L2500178",
#                     "L2500179"
#                 ]
#             },
#             None
#         ),
#         indent=4
#     ))
#
#     # {
#     #     "fastqIdsByLibrary": [
#     #         {
#     #             "libraryId": "L2500185",
#     #             "fastqIdList": [
#     #                 "fqr.01JQTJ7DBS6JYSEX4B57CRZMZ3"
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500181",
#     #             "fastqIdList": [
#     #                 "fqr.01JQTJ7GNHFXF53BWASJR4DN04"
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500178",
#     #             "fastqIdList": [
#     #                 "fqr.01JQTJ7E0AGCCT2CTW4VWWCC8D"
#     #             ]
#     #         },
#     #         {
#     #             "libraryId": "L2500179",
#     #             "fastqIdList": [
#     #                 "fqr.01JQTJ7DV956DE8RPVF21FK7DN"
#     #             ]
#     #         }
#     #     ]
#     # }
