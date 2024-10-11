#!/usr/bin/env python

"""
Generate a case from a case object

Environment variables
PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME: The lambda used to collect the auth token

A sequencerrun object will look like this

{
    "runId": "20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959",
    "specimens": [
      {
        "accessionNumber": "caseaccessionnumber",
        "barcode": "GACTGAGTAG+CACTATCAAC",
        "lane": "1",
        "sampleId": "L2301368",
        "sampleType": "DNA"
      }
    ],
    "type": "pairedEnd"
}
"""

# Standard Imports
import logging
from requests import Response
from os import environ


# Local imports
from pieriandx_pipeline_tools.utils.pieriandx_helpers import get_pieriandx_client
from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_pieriandx_env_vars


def handler(event, context):
    # Get inputs
    sequencerrun_creation_obj = event.get("sequencerrun_creation_obj", {})

    set_pieriandx_env_vars()
    pyriandx_client = get_pieriandx_client(
        email=environ['PIERIANDX_USER_EMAIL'],
        token=environ['PIERIANDX_USER_AUTH_TOKEN'],
        instiution=environ['PIERIANDX_INSTITUTION'],
        base_url=environ['PIERIANDX_BASE_URL'],
    )

    response: Response = pyriandx_client._post_api(
        endpoint=f"/sequencerRun",
        data=sequencerrun_creation_obj
    )

    if response.status_code != 200:
        logging.error(f"Failed to create sequencerrun: {response.json()}")
        raise Exception(f"Failed to create sequencerrun: {response.json()}")

    return response.json()

#
# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "sequencerrun_creation_obj": {
#                         "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04405__L2301368__ot__003__20240415abcd0001",
#                         "specimens": [
#                             {
#                                 "accessionNumber": "SBJ04405__L2301368__ot__003",
#                                 "barcode": "GACTGAGTAG-CACTATCAAC",
#                                 "lane": "1",
#                                 "sampleId": "L2301368",
#                                 "sampleType": "DNA"
#                             }
#                         ],
#                         "type": "pairedEnd"
#                     }
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
# # Yields
# # {
# #   "id": "38862"
# # }