#!/usr/bin/env python

"""
Generate a case from a case object

Environment variables
PIERIANDX_AUTH_TOKEN_SECRET_ID: The secret name for the PierianDx Auth Token

An informatics object will look like this

{
    "input": [
      {
        "accessionNumber": "caseaccessionnumber",
        "sequencerRunInfos": [
          {
            "accessionNumber": "caseaccessionnumber",
            "barcode": "GACTGAGTAG+CACTATCAAC",
            "lane": "1",
            "sampleId": "L2301368",
            "sampleType": "DNA"
          }
        ]
      }
    ]
  }
"""

import logging
from os import environ

from pieriandx_pipeline_tools.utils.pieriandx_helpers import get_pieriandx_client
from requests import Response

from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_pieriandx_env_vars


def handler(event, context):
    # Get inputs
    informaticsjob_creation_obj = event.get("informaticsjob_creation_obj", {})
    case_id = event.get("case_id", None)
    set_pieriandx_env_vars()
    pyriandx_client = get_pieriandx_client(
        email=environ['PIERIANDX_USER_EMAIL'],
        token=environ['PIERIANDX_USER_AUTH_TOKEN'],
        instiution=environ['PIERIANDX_INSTITUTION'],
        base_url=environ['PIERIANDX_BASE_URL'],
    )
    response: Response = pyriandx_client._post_api(
        endpoint=f"/case/{case_id}/informaticsJobs",
        data=informaticsjob_creation_obj
    )

    if response.status_code != 200:
        logging.error(f"Failed to create informaticsjob: {response.json()}")
        raise Exception(f"Failed to create informaticsjob: {response.json()}")

    return response.json()

#
# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "informaticsjob_creation_obj": {
#                         "input": [
#                             {
#                                 "accessionNumber": "SBJ04405__L2301368__ot__003",
#                                 "sequencerRunInfos": [
#                                     {
#                                         "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04405__L2301368__ot__003__20240415abcd0001",
#                                         "barcode": "GACTGAGTAG-CACTATCAAC",
#                                         "lane": "1",
#                                         "sampleId": "L2301368",
#                                         "sampleType": "DNA"
#                                     }
#                                 ]
#                             }
#                         ]
#                     },
#                     "case_id": "100938"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
