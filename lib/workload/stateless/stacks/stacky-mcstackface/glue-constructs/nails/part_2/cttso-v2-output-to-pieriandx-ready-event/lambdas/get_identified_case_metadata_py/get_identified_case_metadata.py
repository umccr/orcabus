#!/usr/bin/env python3

"""
Return payload of de-identified case metadata

Payload will look a bit like this:

{
    "case_metadata": {
        "isIdentified": True,
        "caseAccessionNumber": "SBJ04407__L2301368__V2__abcd1234",
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
        "patientInformation": {
            "dateOfBirth": "1970-01-01",
            "firstName": "John",
            "lastName": "Doe"
        },
        "medicalRecordNumbers": {
            "mrn": "3069999",
            "medicalFacility": {
                "facility": "Not Available",
                "hospitalNumber": "99"
            }
        },
        "requestingPhysician": {
            "firstName": "Meredith",
            "lastName": "Gray"
        }
    }
}

"""

# Imports
from typing import Dict

import pytz
from datetime import datetime
import logging

# Set logger
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format='%(asctime)s %(message)s'
)
logger = logging.getLogger()

# Globals
AUS_TIMEZONE = pytz.timezone("Australia/Melbourne")
AUS_TIME = datetime.now(AUS_TIMEZONE)
AUS_TIME_CURRENT_DEFAULT_DICT = {
    "date_accessioned": AUS_TIME.isoformat(timespec='seconds'),
    "date_collected": AUS_TIME.isoformat(timespec='seconds'),
    "date_received": AUS_TIME.isoformat(timespec='seconds'),
}

DEFAULT_REQUESTING_PHYSICIAN = {
    "first_name": "Sean",
    "last_name": "Grimmond"
}

DEFAULT_INDICATION = "NA"
DEFAULT_HOSPITAL_NUMBER = "99"


def handler(event, context) -> Dict:
    # Return payload of de-identified case metadata

    # Get the case accession number from the event
    case_accession_number = event.get("case_accession_number")

    # Get the external specimen id from the event
    external_sample_id = event.get("external_sample_id")
    external_subject_id = event.get("external_subject_id")

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
    # Get the sample reception from the redcap data if it exists
    date_accessioned = redcap_dict.get("date_accessioned", AUS_TIME_CURRENT_DEFAULT_DICT["date_accessioned"])
    date_collected = redcap_dict.get("date_collected", AUS_TIME_CURRENT_DEFAULT_DICT["date_collected"])
    date_received = redcap_dict.get("date_received", AUS_TIME_CURRENT_DEFAULT_DICT["date_received"])

    # Set the sample reception dictionary
    # Set as camel case for event type
    sample_reception = {
        "dateAccessioned": date_accessioned,
        "dateCollected": date_collected,
        "dateReceived": date_received
    }

    # Get the disease code from the event if it exists or
    disease_code = redcap_dict.get("disease_id", event.get("default_disease_code"))

    # Get patient information from redcap
    if redcap_dict is not None:
        patient_information = {
            "dateOfBirth": "1970-01-01",
            "firstName": "Jane" if redcap_dict.get("gender", "female") else "John",
            "lastName": "Doe"
        }
    else:
        patient_information = {
            "dateOfBirth": "1970-01-01",
            "firstName": "John",
            "lastName": "Doe"
        }

    # Get medical record numbers from redcap
    medical_record_numbers = {
        "mrn": external_subject_id,
        "medicalFacility": {
            "facility": "Not Available",
            "hospitalNumber": DEFAULT_HOSPITAL_NUMBER
        }
    }

    # Get requesting physician from redcap
    requesting_physician = {
        "firstName": redcap_dict.get("requesting_physician_first_name", DEFAULT_REQUESTING_PHYSICIAN["first_name"]),
        "lastName": redcap_dict.get("requesting_physician_last_name", DEFAULT_REQUESTING_PHYSICIAN["last_name"])
    }

    # Return the payload
    return {
        "case_metadata": {
            "isIdentified": True,
            "caseAccessionNumber": case_accession_number,
            "externalSpecimenId": external_sample_id,
            "sampleType": sample_type,
            "specimenLabel": specimen_label,
            "indication": indication,
            "diseaseCode": disease_code,
            "specimenCode": specimen_code,
            "sampleReception": sample_reception,
            "patientInformation": patient_information,
            "medicalRecordNumbers": medical_record_numbers,
            "requestingPhysician": requesting_physician
        }
    }
