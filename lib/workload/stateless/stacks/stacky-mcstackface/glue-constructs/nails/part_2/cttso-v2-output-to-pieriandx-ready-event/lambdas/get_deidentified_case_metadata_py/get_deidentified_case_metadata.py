#!/usr/bin/env python3

"""
Return payload of de-identified case metadata

Payload will look a bit like this:

{
  "isIdentified": false,
  "caseAccessionNumber": "SBJ04407__L2400161__V2__abcd1238",
  "externalSpecimenId": "externalspecimenid",
  "sampleType": "PatientCare",
  "specimenLabel": "primarySpecimen",
  "indication": "Test",
  "diseaseCode": 64572001,
  "specimenCode": 122561005,
  "sampleReception": {
    "dateAccessioned": "2021-01-01T00:00:00Z",
    "dateCollected": "2024-02-20T20:17:00Z",
    "dateReceived": "2021-01-01T00:00:00Z"
  },
  "study": {
    "id": "studyid",
    "subjectIdentifier": "subject"
  }
}

"""

# Imports
from typing import Dict

import pytz
from datetime import datetime
import logging


# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals
AUS_TIMEZONE = pytz.timezone("Australia/Melbourne")
AUS_TIME = datetime.now(AUS_TIMEZONE)
AUS_TIME_AS_STR = f"{AUS_TIME.date().isoformat()}T{AUS_TIME.time().isoformat(timespec='seconds')}{AUS_TIME.strftime('%z')}"

DEFAULT_INDICATION = "NA"


def handler(event, context) -> Dict:
    # Return payload of de-identified case metadata

    # Get the case accession number from the event
    case_accession_number = event.get("case_accession_number")

    # Get the external specimen id from the event
    external_sample_id = event.get("external_sample_id")
    external_subject_id = event.get("external_subject_id")
    project_id = event.get("project_id")

    # Get the sample type from the event
    sample_type = event.get("sample_type")

    # Get the specimen label from the event
    specimen_label = event.get("specimen_label")

    # Get the indication from the event
    indication = event.get("indication", DEFAULT_INDICATION)

    # Get the specimen code from the event
    specimen_code = event.get("specimen_code")

    # Get redcap information from the event
    # For deidentified samples, we only need to
    redcap_dict = event.get("redcap_dict", None)
    if redcap_dict is None:
        redcap_dict = {}

    # Get the sample reception from the redcap data if it exists
    date_accessioned = redcap_dict.get("date_accessioned", AUS_TIME_AS_STR)
    date_collected = redcap_dict.get("date_collected", AUS_TIME_AS_STR)
    date_received = redcap_dict.get("date_received", AUS_TIME_AS_STR)

    # Set the sample reception dictionary
    # Set as camel case for event type
    sample_reception = {
        "dateAccessioned": date_accessioned,
        "dateCollected": date_collected,
        "dateReceived": date_received
    }

    # Get the disease code from the event if it exists or
    disease_code = redcap_dict.get("disease_id", event.get("default_disease_code"))

    # Return the payload
    return {
        "case_metadata": {
            "isIdentified": False,
            "caseAccessionNumber": case_accession_number,
            "externalSpecimenId": external_sample_id,
            "sampleType": sample_type,
            "specimenLabel": specimen_label,
            "indication": indication,
            "diseaseCode": disease_code,
            "specimenCode": specimen_code,
            "sampleReception": sample_reception,
            "study": {
                "id": project_id,
                "subjectIdentifier": external_subject_id
            }
        }
    }


# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "specimen_label": "primarySpecimen",
#                     "indication": None,
#                     "specimen_code": "122561005",
#                     "redcap_dict": None,
#                     "external_subject_id": "CMM1pc-10646259ilm",
#                     "default_disease_code": 55342001,
#                     "external_sample_id": "SSq-CompMM-1pc-10646259ilm",
#                     "case_accession_number": "L2400160__V2__20241003fc695a2c",
#                     "sample_type": "patient_care_sample"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "case_metadata": {
#     #     "case_metadata": {
#     #         "isIdentified": false,
#     #         "caseAccessionNumber": "L2400160__V2__20241003fc695a2c",
#     #         "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#     #         "sampleType": "patient_care_sample",
#     #         "specimenLabel": "primarySpecimen",
#     #         "indication": null,
#     #         "diseaseCode": 55342001,
#     #         "specimenCode": "122561005",
#     #         "sampleReception": {
#     #             "dateAccessioned": "2024-10-04T09:17:27+1000",
#     #             "dateCollected": "2024-10-04T09:17:27+1000",
#     #             "dateReceived": "2024-10-04T09:17:27+1000"
#     #         },
#     #         "study": {
#     #             "id": null,
#     #             "subjectIdentifier": "CMM1pc-10646259ilm"
#     #         }
#     #     }
#     # }