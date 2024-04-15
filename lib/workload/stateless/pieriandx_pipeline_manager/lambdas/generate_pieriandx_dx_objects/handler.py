#!/usr/bin/env python3

"""
Tackle workflow inputs.

By far the most complicated lambda of the lot.

Expects event input in the following syntax (how this is built is someone else's problem)

* dag: Object
  * name: string  # The name of this case dag
  * description: string  # The description of this case dag
* case_metadata: Object
  * panel_name: string  # The name of this case’s panel
  * specimen_label: string  # The mapping to the panels specimen scheme
  * sample_type: Enum  # patientcare, clinical_trial, validation, proficiency_testing
  * indication: String  # Optional input
  * disease: Object
    * code: string  # The disease id
    * label: string  # The name of the disease (optional)
  * is_identified: bool  # Boolean
  * case_accession_number: string - must be unique - uses syntax SBJID__LIBID__NNN
  * specimen_type:
    * code: string   # The SNOMED-CT term for a specimen type
    * label: Optional label for the specimen type
  * external_specimen_id: string  # The external specimen id
  * date_accessioned: Datetime  # The date the case was accessioned
  * date_collected:  Datetime  # The date the specimen was collected
  * date_received:  Datetime  # The date the specimen was received
  * gender:  Enum  # unknown, male, femail, unspecified, other, ambiguous, not_applicable
  * ethnicity:  Enum  # unknown, hispanic_or_latino, not_hispanic_or_latino, not_reported
  * race:  Enum  # american_indian_or_alaska_native, asian, black_or_african_american, native_hawaiian_or_other_pacific_islander, not_reported, unknown, white

  > Note: If the case is de-identified, the following fields are required
  * study_id:  String  # Only required if is_identified is false
  * study_subject_identifier:  String  # Only required if is_identified is false

  > Note: If the case is identified, the following fields are required
  * date_of_birth:  Datetime  # Only required if is_identified is true
  * first_name:  String  # Only required if is_identified is true
  * last_name:  String  # Only required if is_identified is true
  * medical_record_numbers:  Object  # Only required if is_identified is true
    * mrn: string  # The medical record number
    * medical_facility: Object
      * facility: string  # The name of the facility
      * hospital_number: string  # The hospital number
  * requesting_physician:  Object
    * first_name: string
    * last_name: string

* data_files:  Object
  * microsat_output:  uri
  * tmb_metrics:  uri
  * cnv:  uri
  * hard_filtered:  uri
  * fusions:  uri
  * metrics_output:  uri

* samplesheet_b64gz:  str
* instrument_run_id:  str
* portal_run_id:  str
* sequencerrun_s3_prefix:  str

We then use pydantic to validate the input and generate the following outputs

* case_creation_obj: A CaseCreation object
* sequencerrun_creation_obj: A SequencerrunCreation object
* informaticsjob_creation_obj: An InformaticsjobCreation object
* data_files: List of DataFile objects (each containing a src_uri, dest_uri and file_type)
* sequencerrun_s3_path_root: The root s3 path we will upload data to.
* This is the same as the input sequencerrun_s3_path but we will extend the run id to it
"""

import logging
import pandas as pd

from pieriandx_pipeline_tools.pieriandx_classes.data_file import DataFile, DataType
from pieriandx_pipeline_tools.utils.samplesheet_helpers import read_v2_samplesheet

from pieriandx_pipeline_tools.pieriandx_classes.physician import Physician
from pieriandx_pipeline_tools.pieriandx_classes.sequencerrun import SequencerrunCreation
from pieriandx_pipeline_tools.pieriandx_classes.informaticsjob import InformaticsjobCreation
from pieriandx_pipeline_tools.pieriandx_classes.specimen_sequencer_info import SpecimenSequencerInfo
from pieriandx_pipeline_tools.pieriandx_classes.dag import Dag
from pieriandx_pipeline_tools.pieriandx_classes.disease import Disease
from pieriandx_pipeline_tools.pieriandx_classes.medical_record_number import MedicalRecordNumber
from pieriandx_pipeline_tools.pieriandx_classes.medical_facility import MedicalFacility

from pieriandx_pipeline_tools.pieriandx_enums.sequencing_type import SequencingType
from pieriandx_pipeline_tools.pieriandx_enums.sample_type import SampleType


TOP_LEVEL_KEYS = [
    "dag",
    "case_metadata",
    "data_files",
    "samplesheet_b64gz",
    "instrument_run_id",
    "portal_run_id",
    "sequencerrun_s3_path_root",
]

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(event, context):
    # Basic housekeeping
    if event is None:
        raise ValueError("Event is required")
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")

    # Check for top level keys
    if not all([key in event for key in TOP_LEVEL_KEYS]):
        logger.error(f"Could not find keys {' '.join([key for key in TOP_LEVEL_KEYS if key not in event])}")
        raise ValueError("Event is missing required top level keys")

    # Read samplesheet - we need this for the sequencer run infos
    v2_samplesheet_dict = read_v2_samplesheet(event.get("samplesheet_b64gz"))

    # Collect the tso500l_data section
    if not len(v2_samplesheet_dict.get("tso500l_data")) == 1:
        logger.error("Should only be one item in the tso500l data section")
        raise ValueError

    tso500l_data_samplesheet_obj = v2_samplesheet_dict.get("tso500l_data")[0]

    if event.get("case_metadata").get("is_identified"):
        from pieriandx_pipeline_tools.pieriandx_classes.case import IdentifiedCaseCreation as CaseCreation
        from pieriandx_pipeline_tools.pieriandx_classes.specimen import IdentifiedSpecimen as Specimen
    else:
        from pieriandx_pipeline_tools.pieriandx_classes.case import DeIdentifiedCaseCreation as CaseCreation
        from pieriandx_pipeline_tools.pieriandx_classes.specimen import DeIdentifiedSpecimen as Specimen

    # Other imports
    case_creation_obj = CaseCreation(
        # Standard case collection
        dag=Dag(**event.get("dag")),
        disease=Disease(**event.get("case_metadata").get("disease")),
        indication=event.get("case_metadata").get("indication", None),
        panel_name=event.get("case_metadata").get("panel_name"),
        sample_type=SampleType(event.get("case_metadata").get("sample_type")),
        # Identified only fields
        requesting_physician=Physician(**event.get("case_metadata").get("requesting_physician")),
        # Specimen collection
        specimen=Specimen(
            # Standard specimen collection
            case_accession_number=event.get("case_metadata").get("case_accession_number"),
            date_accessioned=pd.to_datetime(event.get("case_metadata").get("date_accessioned")),
            date_received=pd.to_datetime(event.get("case_metadata").get("date_received")),
            date_collected=pd.to_datetime(event.get("case_metadata").get("date_collected")),
            external_specimen_id=event.get("case_metadata").get("external_specimen_id"),
            specimen_label=event.get("case_metadata").get("specimen_label"),
            gender=event.get("case_metadata").get("gender", None),
            ethnicity=event.get("case_metadata").get("ethnicity", None),
            race=event.get("case_metadata").get("race", None),
            specimen_type=event.get("case_metadata").get("specimen_type"),
            # Identified only fields
            date_of_birth=pd.to_datetime(event.get("case_metadata").get("date_of_birth", None)),
            first_name=event.get("case_metadata").get("first_name", None),
            last_name=event.get("case_metadata").get("last_name", None),
            medical_record_number=MedicalRecordNumber(
                mrn=event.get("case_metadata").get("medical_record_numbers").get("mrn"),
                medical_facility=MedicalFacility(
                    facility=event.get("case_metadata").get("medical_record_numbers").get("medical_facility").get("facility"),
                    hospital_number=event.get("case_metadata").get("medical_record_numbers").get("medical_facility").get("hospital_number")
                )
            ) if event.get("case_metadata").get("is_identified") else None,
            # De-identified only fields
            study_id=event.get("case_metadata").get("study_id", None),
            study_subject_identifier=event.get("case_metadata").get("study_subject_identifier", None)
        )
    )

    # Set run id (used for sequencer run path)
    run_id = "__".join(
        [
            event.get("instrument_run_id"),
            event.get("case_metadata").get("case_accession_number"),
            event.get('portal_run_id')
        ]
    )

    # Get sequencer runinfo object (used for both sequencer run and informatics job creation)
    specimen_sequencer_info = SpecimenSequencerInfo(
        run_id=run_id,
        case_accession_number=event.get("case_metadata").get("case_accession_number"),
        barcode=f"{tso500l_data_samplesheet_obj.get('index')}-{tso500l_data_samplesheet_obj.get('index2')}",
        lane=tso500l_data_samplesheet_obj.get("lane"),
        sample_id=tso500l_data_samplesheet_obj.get("sample_id"),
        sample_type=tso500l_data_samplesheet_obj.get("sample_type")
    )

    # Sequencerrun creation object
    sequencer_run_creation = SequencerrunCreation(
        run_id=run_id,
        specimen_sequence_info=specimen_sequencer_info,
        sequencing_type=SequencingType.PAIRED_END
    )

    # Informatics job
    informatics_job_creation = InformaticsjobCreation(
        case_accession_number=event.get("case_metadata").get("case_accession_number"),
        specimen_sequencer_run_info=specimen_sequencer_info
    )

    # Add sequencerrun path
    sequencerrun_s3_path = f"{event.get('sequencerrun_s3_path_root').rstrip('/')}/{run_id}"

    # Data files
    data_files = list(
        map(
            lambda data_file_iter_kv: DataFile(
                sequencerrun_path_root=sequencerrun_s3_path,
                file_type=DataType(data_file_iter_kv[0]),
                sample_id=tso500l_data_samplesheet_obj.get("sample_id"),
                src_uri=data_file_iter_kv[1],
                contents=None
            ),
            event.get("data_files").items()
        )
    )

    # Add vcfworkflow.txt

    return {
        "case_creation_obj": case_creation_obj.to_dict(),
        "sequencerrun_creation_obj": sequencer_run_creation.to_dict(),
        "informaticsjob_creation_obj": informatics_job_creation.to_dict(),
        "data_files": list(map(lambda data_file_iter: data_file_iter.to_dict(), data_files)),
        "sequencerrun_s3_path": sequencerrun_s3_path
    }


if __name__ == "__main__":
    import json
    print(
        json.dumps(
            handler(
                {
                    "dag": {
                        "name": "dagname",
                        "description": "dagdescription"
                    },
                    "case_metadata": {
                        "panel_name": "panelname",
                        "specimen_label": "primarySpecimen",
                        "sample_type": "patientcare",
                        "indication": "indication",
                        "disease": {
                            "code": "diseasecode",
                            "label": "diseaselabel"
                        },
                        "is_identified": True,
                        "case_accession_number": "caseaccessionnumber",
                        "specimen_type": {
                            "code": "specimentypecode",
                            "label": "specimentypelabel"
                        },
                        "external_specimen_id": "externalspecimenid",
                        "date_accessioned": "2021-01-01T00:00:00Z",
                        "date_collected": "2021-01-01T00:00:00Z",
                        "date_received": "2021-01-01T00:00:00Z",
                        "date_of_birth": "1970-01-01",
                        "first_name": "John",
                        "last_name": "Doe",
                        "medical_record_numbers": {
                            "mrn": "mrn",
                            "medical_facility": {
                                "facility": "facility",
                                "hospital_number": "hospitalnumber"
                            }
                        },
                        "requesting_physician": {
                            "first_name": "Meredith",
                            "last_name": "Gray"
                        }
                    },
                    "data_files": {
                        "microsat_output": "icav2://project-id/path/to/sample-microsat_output.txt",
                        "tmb_metrics": "icav2://project-id/path/to/sample-tmb_metrics.txt",
                        "cnv": "icav2://project-id/path/to/sample-cnv.txt",
                        "hard_filtered": "icav2://project-id/path/to/sample-hard_filtered.txt",
                        "fusions": "icav2://project-id/path/to/sample-fusions.txt",
                        "metrics_output": "icav2://project-id/path/to/sample-metrics_output.txt",
                    },
                    "samplesheet_b64gz": "H4sIAAAAAAAAA42SX0vDMBTF3/cpRp4VktY5/zyFCUXQIto9iEjI7N0abNItyYZj7Lt7065rh3uQ0tLc37npybndDYZDUoDMwZK74Q5XuJ6rEsS8slp6sQHrVGUQRhcNtWsjjNSAJZK5lblMYfaa8ihmjMWXz08Ab9mrYNdptYlicmhSxnm71mC88Ntl3YtcvsGKoGAfVMSiDde5CEvBxNf2q4RQZiN20SPROaJMDj8nTfSE9Jvo8cPeVSNKS+HAe2UWPQ8yl0sPVjRegutJlmQTvDKe8Qle+Nqe8UQc/VM8g0JuVLUO8RNvlW4FWhml11qEmoa82bUEs/AFSuNRK5PuW7iisl60+R1ZhcOzKofu0GQ6Ttk7u4rvHxmt77ZA/qSRSy+x5aPeq8kDqZN6iX+HysNuT1FMWXx9c/Dc4XbGDynvWClNKLJjoZ5JkCUck+JJxhNyCpsUkWJ0nE96dCyaiTZGpg8vlNLbHh+d5TXe4/NzsB/8AvJdybj8AgAA",
                    "sequencerrun_s3_path_root": "s3://pieriandx/melbourne",
                    "instrument_run_id": "20201203_A00123_0001_BHJGJFDS",
                    "portal_run_id": "20240411235959",
                },
                None
            ),
            indent=2
        )
    )
# Yields
# {
#   "case_creation_obj": {
#     "identified": true,
#     "indication": "indication",
#     "panelName": "panelname",
#     "sampleType": "patientcare",
#     "specimens": [
#       {
#         "accessionNumber": "caseaccessionnumber",
#         "dateAccessioned": "2021-01-01T00:00:00Z",
#         "dateReceived": "2021-01-01T00:00:00Z",
#         "datecollected": "2021-01-01T00:00:00Z",
#         "ethnicity": "unknown",
#         "externalSpecimenId": "externalspecimenid",
#         "gender": "unknown",
#         "name": "primarySpecimen",
#         "race": "unknown",
#         "type": {
#           "code": "specimentypecode",
#           "label": "specimentypelabel"
#         },
#         "firstName": "John",
#         "lastName": "Doe",
#         "dateOfBirth": "1970-01-01",
#         "medicalRecordNumbers": [
#           {
#             "mrn": "mrn",
#             "medicalFacility": {
#               "facility": "facility",
#               "hospitalNumber": "hospitalnumber"
#             }
#           }
#         ]
#       }
#     ],
#     "dagDescription": "dagdescription",
#     "dagName": "dagname",
#     "disease": {
#       "code": "diseasecode",
#       "label": "diseaselabel"
#     },
#     "physicians": [
#       {
#         "firstName": "Meredith",
#         "lastName": "Gray"
#       }
#     ]
#   },
#   "sequencerrun_creation_obj": {
#     "runId": "20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959",
#     "specimens": [
#       {
#         "accessionNumber": "caseaccessionnumber",
#         "barcode": "GACTGAGTAG+CACTATCAAC",
#         "lane": "1",
#         "sampleId": "L2301368",
#         "sampleType": "DNA"
#       }
#     ],
#     "type": "pairedEnd"
#   },
#   "informaticsjob_creation_obj": {
#     "input": [
#       {
#         "accessionNumber": "caseaccessionnumber",
#         "sequencerRunInfos": [
#           {
#             "accessionNumber": "caseaccessionnumber",
#             "barcode": "GACTGAGTAG+CACTATCAAC",
#             "lane": "1",
#             "sampleId": "L2301368",
#             "sampleType": "DNA"
#           }
#         ]
#       }
#     ]
#   },
#   "data_files": [
#     {
#       "src_uri": "icav2://project-id/path/to/sample-microsat_output.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.microsat_output.json",
#       "needs_decompression": false,
#       "contents": null
#     },
#     {
#       "src_uri": "icav2://project-id/path/to/sample-tmb_metrics.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.tmb.metrics.csv",
#       "needs_decompression": false,
#       "contents": null
#     },
#     {
#       "src_uri": "icav2://project-id/path/to/sample-cnv.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368_cnv.vcf",
#       "needs_decompression": false,
#       "contents": null
#     },
#     {
#       "src_uri": "icav2://project-id/path/to/sample-hard_filtered.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.hard-filtered.vcf",
#       "needs_decompression": false,
#       "contents": null
#     },
#     {
#       "src_uri": "icav2://project-id/path/to/sample-fusions.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.fusions.csv",
#       "needs_decompression": false,
#       "contents": null
#     },
#     {
#       "src_uri": "icav2://project-id/path/to/sample-metrics_output.txt",
#       "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368_MetricsOutput.tsv",
#       "needs_decompression": false,
#       "contents": null
#     }
#   ],
#   "sequencerrun_s3_path": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959"
# }