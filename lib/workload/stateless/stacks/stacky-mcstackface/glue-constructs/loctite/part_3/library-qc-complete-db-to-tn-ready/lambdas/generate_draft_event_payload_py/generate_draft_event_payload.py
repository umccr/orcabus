#!/usr/bin/env python3

"""
Generate draft event payload for the event

Given the tumor library id and normal library id, generate the inputs for the workflow.

{
    "enable_duplicate_marking": true
    "enable_cnv_somatic": true
    "enable_hrd_somatic": true
    "enable_sv_somatic": true
    "cnv_use_somatic_vc_baf": true,
    "output_prefix_somatic": "<tumor_library_id>",
    "output_prefix_germline": "<normal_library_id>",
    "fastq_list_rows": <normal_fastq_list_rows>,
    "tumor_fastq_list_rows": <tumor_fastq_list_rows>,
}

"""

from typing import Dict
DEFAULT_DRAGEN_REFERENCE_VERSION = "v9-r3"


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """
    subject_id = event['subject_id']
    individual_id = event['individual_id']

    tumor_library_id = event['tumor_library_id']
    normal_library_id = event['normal_library_id']

    tumor_fastq_list_rows: Dict = event['tumor_fastq_list_rows']
    tumor_fastq_list_row_ids: Dict = event['tumor_fastq_list_row_ids']
    fastq_list_rows: Dict = event['fastq_list_rows']
    fastq_list_row_ids: Dict = event['fastq_list_row_ids']

    return {
        "input_event_data": {
            "enableDuplicateMarking": True,
            "enableCnvSomatic": True,
            "enableHrdSomatic": True,
            "enableSvSomatic": True,
            "cnvUseSomaticVcBaf": True,
            "outputPrefixSomatic": tumor_library_id,
            "outputPrefixGermline": normal_library_id,
            "tumorFastqListRows": tumor_fastq_list_rows,
            "fastqListRows": fastq_list_rows,
            "dragenReferenceVersion": DEFAULT_DRAGEN_REFERENCE_VERSION
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "tumorLibraryId": tumor_library_id,
            "normalLibraryId": normal_library_id,
            "tumorFastqListRowIds": tumor_fastq_list_row_ids,
            "normalFastqListRowIds": fastq_list_row_ids
        }
    }
