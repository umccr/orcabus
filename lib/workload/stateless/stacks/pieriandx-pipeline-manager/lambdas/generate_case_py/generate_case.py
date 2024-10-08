#!/usr/bin/env python

"""
Generate a case from a case object

Environment variables
PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME: The secret name for the PierianDx Auth Token 'PierianDx/JwtKey'
PIERIANDX_USER_EMAIL:
PIERIANDX_INSTITUTION
PIERIANDX_BASE_URL

A Case object will look like this

{
    "identified": true,
    "indication": "indication",
    "panelName": "panelname",
    "sampleType": "patientcare",
    "specimens": [
      {
        "accessionNumber": "caseaccessionnumber",
        "dateAccessioned": "2021-01-01TZ:00+Z",
        "dateReceived": "2021-01-01TZ:00+Z",
        "datecollected": "2021-01-01TZ:00+Z",
        "externalSpecimenId": "externalspecimenid",
        "name": "panelspecimenscheme",
        "type": {
          "code": "specimentypecode",
          "label": "specimentypelabel"
        },
        "firstName": "John",
        "lastName": "Doe",
        "dateOfBirth": "1970-01-01",
        "medicalRecordNumbers": [
          {
            "mrn": "mrn",
            "medicalFacility": {
              "facility": "facility",
              "hospitalNumber": "hospitalnumber"
            }
          }
        ]
      }
    ],
    "dagDescription": "dagdescription",
    "dagName": "dagname",
    "disease": {
      "code": "diseasecode",
      "label": "diseaselabel"
    },
    "physicians": [
      {
        "firstName": "Meredith",
        "lastName": "Gray"
      }
    ]
    }
"""

import logging
from os import environ

from pieriandx_pipeline_tools.utils.pieriandx_helpers import get_pieriandx_client
from requests import Response, HTTPError

from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_pieriandx_env_vars


def handler(event, context):
    case_creation_obj = event.get("case_creation_obj", {})
    set_pieriandx_env_vars()
    pyriandx_client = get_pieriandx_client(
        email=environ['PIERIANDX_USER_EMAIL'],
        token=environ['PIERIANDX_USER_AUTH_TOKEN'],
        instiution=environ['PIERIANDX_INSTITUTION'],
        base_url=environ['PIERIANDX_BASE_URL'],
    )

    try:
        response: Response = pyriandx_client._post_api(
            endpoint="/case",
            data=case_creation_obj
        )
        response.raise_for_status()
    except HTTPError as e:
        logging.error(f"Failed to create case: {e}")
        raise Exception(f"Failed to create case: {e}")

    if response.status_code != 200:
        logging.error(f"Failed to create case: {response.json()}")
        raise Exception(f"Failed to create case: {response.json()}")

    return response.json()


# if __name__ == "__main__":
#     import json
#
#     logging.basicConfig(level=logging.DEBUG)
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PIERIANDX_BASE_URL'] = "https://app.uat.pieriandx.com/cgw-api/v2.0.0"
#     environ['PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME'] = "collectPierianDxAccessToken"
#     environ['PIERIANDX_INSTITUTION'] = "melbournetest"
#     environ['PIERIANDX_USER_EMAIL'] = "services@umccr.org"
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "case_creation_obj": {
#                         "identified": True,
#                         "indication": "Test",
#                         "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # // pragma: allowlist secret
#                         "sampleType": "patientcare",
#                         "specimens": [
#                             {
#                                 "accessionNumber": "SBJ04407__L2301368__V2__abcd12345",
#                                 "dateAccessioned": "2021-01-01T00:00:00Z",
#                                 "dateReceived": "2021-01-01T00:00:00Z",
#                                 "datecollected": "2024-02-20T20:17:00Z",
#                                 "externalSpecimenId": "externalspecimenid",
#                                 "name": "primarySpecimen",
#                                 "type": {
#                                     "code": "122561005",
#                                     "label": "Blood specimen from patient"
#                                 },
#                                 "firstName": "John",
#                                 "lastName": "Doe",
#                                 "dateOfBirth": "1970-01-01",
#                                 "medicalRecordNumbers": [
#                                     {
#                                         "mrn": "3069999",
#                                         "medicalFacility": {
#                                             "facility": "Not Available",
#                                             "hospitalNumber": "99"
#                                         }
#                                     }
#                                 ]
#                             }
#                         ],
#                         "dagDescription": "tso500_ctdna_workflow",
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "disease": {
#                             "code": "64572001",
#                             "label": "Disease"
#                         },
#                         "physicians": [
#                             {
#                                 "firstName": "Meredith",
#                                 "lastName": "Gray"
#                             }
#                         ]
#                     },
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   'id': '100937',
#     #   'accessionNumber': 'SBJ04405__L2301368__ot__002',
#     #   'dateCreated': '2024-04-14'
#     # }

#
# if __name__ == "__main__":
#     import json
#
#     logging.basicConfig(level=logging.DEBUG)
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PIERIANDX_BASE_URL'] = "https://app.uat.pieriandx.com/cgw-api/v2.0.0"
#     environ['PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME'] = "collectPierianDxAccessToken"
#     environ['PIERIANDX_INSTITUTION'] = "melbournetest"
#     environ['PIERIANDX_USER_EMAIL'] = "services@umccr.org"
#
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "case_creation_obj": {
#                         "identified": False,
#                         "indication": "NA",
#                         "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # // pragma: allowlist secret
#                         "sampleType": "patientcare",
#                         "specimens": [
#                             {
#                                 "accessionNumber": "L2400160__V2__20241003f3149835",
#                                 "dateAccessioned": "2024-10-04T09:01:32+1000",
#                                 "dateReceived": "2024-10-04T09:01:32+1000",
#                                 "datecollected": "2024-10-04T09:01:32+1000",
#                                 "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#                                 "name": "primarySpecimen",
#                                 "type": {
#                                     "code": "122561005",
#                                     "label": "Blood specimen from patient"
#                                 },
#                                 "studyIdentifier": "Testing",
#                                 "studySubjectIdentifier": "CMM1pc-10646259ilm"
#                             }
#                         ],
#                         "dagDescription": "tso500_ctdna_workflow",
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "disease": {
#                             "code": "55342001",
#                             "label": "Neoplastic disease"
#                         }
#                     }
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   'id': '100937',
#     #   'accessionNumber': 'SBJ04405__L2301368__ot__002',
#     #   'dateCreated': '2024-04-14'
#     # }
