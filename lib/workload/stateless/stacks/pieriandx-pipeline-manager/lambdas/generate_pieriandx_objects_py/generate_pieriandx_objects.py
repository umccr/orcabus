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

from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_icav2_env_vars
from pieriandx_pipeline_tools.pieriandx_classes.data_file import DataFile, DataType
from pieriandx_pipeline_tools.pieriandx_enums.specimen_type import SpecimenType
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
    "panel_name",
    "instrument_run_id",
    "portal_run_id",
    "sequencerrun_s3_path_root",
]

# Set basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def handler(event, context):
    # Set env vars
    set_icav2_env_vars()

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
    v2_samplesheet_dict = read_v2_samplesheet(event.get("samplesheet_uri"))

    # Collect the tso500l_data section
    if not len(v2_samplesheet_dict.get("tso500l_data")) == 1:
        logger.error("Should only be one item in the tso500l data section")
        raise ValueError

    tso500l_data_samplesheet_obj = v2_samplesheet_dict.get("tso500l_data")[0]
    sample_name = tso500l_data_samplesheet_obj['sample_id']

    if event.get("case_metadata").get("isIdentified"):
        from pieriandx_pipeline_tools.pieriandx_classes.case import IdentifiedCaseCreation as CaseCreation
        from pieriandx_pipeline_tools.pieriandx_classes.specimen import IdentifiedSpecimen as Specimen
    else:
        from pieriandx_pipeline_tools.pieriandx_classes.case import DeIdentifiedCaseCreation as CaseCreation
        from pieriandx_pipeline_tools.pieriandx_classes.specimen import DeIdentifiedSpecimen as Specimen

    # Other imports
    case_creation_obj = CaseCreation(
        # Standard case collection
        dag=Dag(
            name=event.get("dag").get("dagName"),
            description=event.get("dag").get("dagDescription")
        ),
        disease=Disease(code=int(event.get("case_metadata").get("diseaseCode"))),
        indication=event.get("case_metadata").get("indication", None),
        panel_name=event.get("panel_name"),
        sample_type=SampleType(event.get("case_metadata").get("sampleType").lower()),
        # Identified only fields
        requesting_physician=(
            Physician(
                first_name=event.get("case_metadata").get("requestingPhysician").get("firstName"),
                last_name=event.get("case_metadata").get("requestingPhysician").get("lastName")
            ) if event.get("case_metadata").get("isIdentified")
            else None
        ),
        # Specimen collection
        specimen=Specimen(
            # Standard specimen collection
            case_accession_number=event.get("case_metadata").get("caseAccessionNumber"),
            date_accessioned=pd.to_datetime(
                event.get("case_metadata").get("sampleReception").get("dateAccessioned"),
                utc=True
            ),
            date_received=pd.to_datetime(
                event.get("case_metadata").get("sampleReception").get("dateReceived"),
                utc=True
            ),
            date_collected=pd.to_datetime(
                event.get("case_metadata").get("sampleReception").get("dateCollected"),
                utc=True
            ),
            external_specimen_id=event.get("case_metadata").get("externalSpecimenId"),
            specimen_label=event.get("case_metadata").get("specimenLabel"),
            gender=event.get("case_metadata").get("gender", None),
            ethnicity=event.get("case_metadata").get("ethnicity", None),
            race=event.get("case_metadata").get("race", None),
            specimen_type=SpecimenType(code=int(event.get("case_metadata").get("specimenCode"))),
            # Identified only fields
            date_of_birth=pd.to_datetime(
                event.get("case_metadata").get("patientInformation", {}).get("dateOfBirth", None)
            ),
            first_name=event.get("case_metadata").get("patientInformation", {}).get("firstName", None),
            last_name=event.get("case_metadata").get("patientInformation", {}).get("lastName", None),
            medical_record_number=MedicalRecordNumber(
                mrn=event.get("case_metadata").get("medicalRecordNumbers").get("mrn"),
                medical_facility=(
                    MedicalFacility(
                        facility=(
                            event.get("case_metadata")
                            .get("medicalRecordNumbers")
                            .get("medicalFacility")
                            .get("facility")
                        ),
                        hospital_number=(
                            event.get("case_metadata")
                            .get("medicalRecordNumbers")
                            .get("medicalFacility")
                            .get("hospitalNumber")
                        )
                    )
                )
            ) if event.get("case_metadata").get("isIdentified") else None,
            # De-identified only fields
            study_identifier=event.get("case_metadata").get("study", {}).get("id", None),
            study_subject_identifier=event.get("case_metadata").get("study", {}).get("subjectIdentifier", None)
        )
    )

    # Set run id (used for sequencer run path)
    run_id = "__".join(
        [
            event.get("instrument_run_id"),
            event.get("case_metadata").get("caseAccessionNumber"),
            event.get('portal_run_id')
        ]
    )

    # Get sequencer runinfo object (used for both sequencer run and informatics job creation)
    specimen_sequencer_info = SpecimenSequencerInfo(
        run_id=run_id,
        case_accession_number=event.get("case_metadata").get("caseAccessionNumber"),
        barcode=f"{tso500l_data_samplesheet_obj.get('index')}-{tso500l_data_samplesheet_obj.get('index2')}",
        lane=tso500l_data_samplesheet_obj.get("lane", 1),
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
        case_accession_number=event.get("case_metadata").get("caseAccessionNumber"),
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
            filter(
                lambda data_file_iter_kv: (
                        data_file_iter_kv[0] in
                        list(map(lambda enum_iter: enum_iter.value, DataType._member_map_.values()))
                ),
                event.get("data_files").items()
            )
        )
    )

    # Return list of objects for downstream sfns to consume
    return {
        "case_creation_obj": case_creation_obj.to_dict(),
        "sequencerrun_creation_obj": sequencer_run_creation.to_dict(),
        "informaticsjob_creation_obj": informatics_job_creation.to_dict(),
        "data_files": list(map(lambda data_file_iter: data_file_iter.to_dict(), data_files)),
        "sequencerrun_s3_path": sequencerrun_s3_path,
        "sample_name": sample_name,
    }



#  # Idenitified Patient
# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "sequencerrun_s3_path_root": "s3://pdx-cgwxfer-test/melbournetest",
#                     "portal_run_id": "abcd1234",
#                     "samplesheet_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
#                     "panel_name": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#                     "dag": {
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "dagDescription": "tso500_ctdna_workflow"
#                     },
#                     "data_files": {
#                         "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2301368/L2301368.microsat_output.json",
#                         "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2301368/L2301368.tmb.metrics.csv",
#                         "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.cnv.vcf.gz",
#                         "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.hard-filtered.vcf.gz",
#                         "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_Fusions.csv",
#                         "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_MetricsOutput.tsv",
#                         "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                     },
#                     "case_metadata": {
#                         "isIdentified": True,
#                         "caseAccessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#                         "externalSpecimenId": "externalspecimenid",
#                         "sampleType": "PatientCare",
#                         "specimenLabel": "primarySpecimen",
#                         "indication": "Test",
#                         "diseaseCode": 64572001,
#                         "specimenCode": 122561005,
#                         "sampleReception": {
#                             "dateAccessioned": "2021-01-01",
#                             "dateCollected": "2024-02-20",
#                             "dateReceived": "2021-01-01"
#                         },
#                         "patientInformation": {
#                             "dateOfBirth": "1970-01-01",
#                             "firstName": "John",
#                             "lastName": "Doe"
#                         },
#                         "medicalRecordNumbers": {
#                             "mrn": "3069999",
#                             "medicalFacility": {
#                                 "facility": "Not Available",
#                                 "hospitalNumber": "99"
#                             }
#                         },
#                         "requestingPhysician": {
#                             "firstName": "Meredith",
#                             "lastName": "Gray"
#                         }
#                     },
#                     "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   "case_creation_obj": {
#     #     "identified": true,
#     #     "indication": "Test",
#     #     "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#     #     "sampleType": "patientcare",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "dateAccessioned": "2021-01-01T00:00:00Z",
#     #         "dateReceived": "2021-01-01T00:00:00Z",
#     #         "datecollected": "2024-02-20T00:00:00Z",
#     #         "externalSpecimenId": "externalspecimenid",
#     #         "name": "primarySpecimen",
#     #         "type": {
#     #           "code": "122561005",
#     #           "label": "Blood specimen from patient"
#     #         },
#     #         "firstName": "John",
#     #         "lastName": "Doe",
#     #         "dateOfBirth": "1970-01-01",
#     #         "medicalRecordNumbers": [
#     #           {
#     #             "mrn": "3069999",
#     #             "medicalFacility": {
#     #               "facility": "Not Available",
#     #               "hospitalNumber": "99"
#     #             }
#     #           }
#     #         ]
#     #       }
#     #     ],
#     #     "dagDescription": "tso500_ctdna_workflow",
#     #     "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#     #     "disease": {
#     #       "code": "64572001",
#     #       "label": "Disease"
#     #     },
#     #     "physicians": [
#     #       {
#     #         "firstName": "Meredith",
#     #         "lastName": "Gray"
#     #       }
#     #     ]
#     #   },
#     #   "sequencerrun_creation_obj": {
#     #     "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "barcode": "CCATCATTAG-AGAGGCAACC",
#     #         "lane": "1",
#     #         "sampleId": "L2400161",
#     #         "sampleType": "DNA"
#     #       }
#     #     ],
#     #     "type": "pairedEnd"
#     #   },
#     #   "informaticsjob_creation_obj": {
#     #     "input": [
#     #       {
#     #         "accessionNumber": "SBJ04407__L2301368__V2__abcd1234",
#     #         "sequencerRunInfos": [
#     #           {
#     #             "runId": "231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #             "barcode": "CCATCATTAG-AGAGGCAACC",
#     #             "lane": "1",
#     #             "sampleId": "L2400161",
#     #             "sampleType": "DNA"
#     #           }
#     #         ]
#     #       }
#     #     ]
#     #   },
#     #   "data_files": [
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2301368/L2301368.microsat_output.json",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.microsat_output.json",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2301368/L2301368.tmb.metrics.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.tmb.metrics.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.cnv.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.cnv.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368.hard-filtered.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161.hard-filtered.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_Fusions.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161_Fusions.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2301368/L2301368_MetricsOutput.tsv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234/Data/Intensities/BaseCalls/L2400161_MetricsOutput.tsv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     }
#     #   ],
#     #   "sequencerrun_s3_path": "s3://pdx-cgwxfer-test/melbournetest/231116_A01052_0172_BHVLM5DSX7__SBJ04407__L2301368__V2__abcd1234__abcd1234",
#     #   "sample_name": "L2400161"
#     # }

#
# #  # De-Idenitified Patient
# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "sequencerrun_s3_path_root": "s3://pdx-cgwxfer-test/melbournetest",
#                     "portal_run_id": "20241003f44a5496",
#                     "samplesheet_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
#                     "panel_name": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#                     "dag": {
#                         "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#                         "dagDescription": "tso500_ctdna_workflow"
#                     },
#                     "data_files": {
#                         "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/DragenCaller/L2400160/L2400160.microsat_output.json",
#                         "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/Tmb/L2400160/L2400160.tmb.metrics.csv",
#                         "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.cnv.vcf.gz",
#                         "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.hard-filtered.vcf.gz",
#                         "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_Fusions.csv",
#                         "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_MetricsOutput.tsv",
#                         "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
#                     },
#                     "case_metadata": {
#                         "isIdentified": False,
#                         "caseAccessionNumber": "L2400160__V2__20241003f44a5496",
#                         "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#                         "sampleType": "patientcare",
#                         "specimenLabel": "primarySpecimen",
#                         "indication": None,
#                         "diseaseCode": 55342001,
#                         "specimenCode": "122561005",
#                         "sampleReception": {
#                             "dateAccessioned": "2024-10-03",
#                             "dateCollected": "2024-10-03",
#                             "dateReceived": "2024-10-03"
#                         },
#                         "study": {
#                             "id": "Testing",
#                             "subjectIdentifier": "CMM1pc-10646259ilm"
#                         }
#                     },
#                     "instrument_run_id": "240229_A00130_0288_BH5HM2DSXC"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # Yields
#     # {
#     #   "case_creation_obj": {
#     #     "identified": false,
#     #     "panelName": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne",  # pragma: allowlist secret
#     #     "sampleType": "patientcare",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "L2400160__V2__20241003f44a5496",
#     #         "dateAccessioned": "2024-10-03T00:00:00Z",
#     #         "dateReceived": "2024-10-03T00:00:00Z",
#     #         "datecollected": "2024-10-03T00:00:00Z",
#     #         "externalSpecimenId": "SSq-CompMM-1pc-10646259ilm",
#     #         "name": "primarySpecimen",
#     #         "type": {
#     #           "code": "122561005",
#     #           "label": "Blood specimen from patient"
#     #         },
#     #         "studyIdentifier": "Testing",
#     #         "studySubjectIdentifier": "CMM1pc-10646259ilm"
#     #       }
#     #     ],
#     #     "dagDescription": "tso500_ctdna_workflow",
#     #     "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
#     #     "disease": {
#     #       "code": "55342001",
#     #       "label": "Neoplastic disease"
#     #     }
#     #   },
#     #   "sequencerrun_creation_obj": {
#     #     "runId": "240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#     #     "specimens": [
#     #       {
#     #         "accessionNumber": "L2400160__V2__20241003f44a5496",
#     #         "barcode": "AGAGGCAACC-CCATCATTAG",
#     #         "lane": "1",
#     #         "sampleId": "L2400160",
#     #         "sampleType": "DNA"
#     #       }
#     #     ],
#     #     "type": "pairedEnd"
#     #   },
#     #   "informaticsjob_creation_obj": {
#     #     "input": [
#     #       {
#     #         "accessionNumber": "L2400160__V2__20241003f44a5496",
#     #         "sequencerRunInfos": [
#     #           {
#     #             "runId": "240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#     #             "barcode": "AGAGGCAACC-CCATCATTAG",
#     #             "lane": "1",
#     #             "sampleId": "L2400160",
#     #             "sampleType": "DNA"
#     #           }
#     #         ]
#     #       }
#     #     ]
#     #   },
#     #   "data_files": [
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/DragenCaller/L2400160/L2400160.microsat_output.json",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.microsat_output.json",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Logs_Intermediates/Tmb/L2400160/L2400160.tmb.metrics.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.tmb.metrics.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.cnv.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.cnv.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160.hard-filtered.vcf.gz",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160.hard-filtered.vcf",
#     #       "needs_decompression": true,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_Fusions.csv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160_Fusions.csv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     },
#     #     {
#     #       "src_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20241003ead8ad9f/Results/L2400160/L2400160_MetricsOutput.tsv",
#     #       "dest_uri": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496/Data/Intensities/BaseCalls/L2400160_MetricsOutput.tsv",
#     #       "needs_decompression": false,
#     #       "contents": null
#     #     }
#     #   ],
#     #   "sequencerrun_s3_path": "s3://pdx-cgwxfer-test/melbournetest/240229_A00130_0288_BH5HM2DSXC__L2400160__V2__20241003f44a5496__20241003f44a5496",
#     #   "sample_name": "L2400160"
#     # }
