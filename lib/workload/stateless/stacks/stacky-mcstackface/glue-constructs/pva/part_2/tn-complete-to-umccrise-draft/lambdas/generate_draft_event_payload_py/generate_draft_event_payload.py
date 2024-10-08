#!/usr/bin/env python3

"""
Generate draft event payload for the umccrise event

Given the following parameters, generate the draft payload for the umccrise event

{
    subject_id
    tumor_library_id
    normal_library_id
    tumor_fastq_list_row_ids
    normal_fastq_list_row_ids
    dragen_somatic_output_s3_uri
    dragen_germline_output_s3_uri
}

We need the inputs

subjectId
dragenSomaticLibraryId
dragenGermlineLibraryId
dragenSomaticOutputUri
dragenGermlineOutputUri

And tags

subjectId
tumorLibraryId
normalLibraryId
tumorFastqListRowIds
normalFastqListRowIds


"""
from typing import List, Dict


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
    dragen_somatic_output_s3_uri = event['dragen_somatic_output_s3_uri']
    dragen_germline_output_s3_uri = event['dragen_germline_output_s3_uri']
    tumor_fastq_list_row_ids: List[str] = event['tumor_fastq_list_row_ids']
    normal_fastq_list_row_ids: List[str] = event['normal_fastq_list_row_ids']

    return {
        "input_event_data": {
            "subjectId": individual_id,
            "dragenSomaticLibraryId": tumor_library_id,
            "dragenGermlineLibraryId": normal_library_id,
            "dragenSomaticOutputUri": dragen_somatic_output_s3_uri,
            "dragenGermlineOutputUri": dragen_germline_output_s3_uri,
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "tumorLibraryId": tumor_library_id,
            "normalLibraryId": normal_library_id,
            "tumorFastqListRowIds": tumor_fastq_list_row_ids,
            "normalFastqListRowIds": normal_fastq_list_row_ids
        }
    }
