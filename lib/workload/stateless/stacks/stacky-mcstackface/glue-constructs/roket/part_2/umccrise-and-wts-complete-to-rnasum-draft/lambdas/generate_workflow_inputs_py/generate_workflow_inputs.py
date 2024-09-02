#!/usr/bin/env python3

"""
Generate workflow inputs

Input:
arriba_output_uri
dragen_wts_output_uri
umccrise_output_uri
wts_tumor_library_id
subject_id

Output:
input_event_data
event_tags
"""


def handler(event, context):
    """


    :param event:
    :param context:
    :return:
    """

    # Inputs
    arriba_output_uri = event['arriba_output_uri']
    dragen_wts_output_uri = event['dragen_wts_output_uri']
    umccrise_output_uri = event['umccrise_output_uri']
    wts_tumor_library_id = event['wts_tumor_library_id']
    wgs_tumor_library_id = event['wgs_tumor_library_id']
    wgs_normal_library_id = event['wgs_normal_library_id']
    wts_tumor_fastq_list_row_ids = event['wts_tumor_fastq_list_row_ids']
    wgs_tumor_fastq_list_row_ids = event['wgs_tumor_fastq_list_row_ids']
    wgs_normal_fastq_list_row_ids = event['wgs_normal_fastq_list_row_ids']
    subject_id = event['subject_id']

    # Outputs
    input_event_data = {
        "arribaUri": arriba_output_uri,
        "dragenTranscriptomeUri": dragen_wts_output_uri,
        "umccriseUri": umccrise_output_uri,
        "wtsTumorLibraryId": wts_tumor_library_id,
        "subjectId": subject_id
    }

    event_tags = {
        "subjectId": subject_id,
        "wtsTumorLibraryId": wts_tumor_library_id,
        "wgsTumorLibraryId": wgs_tumor_library_id,
        "wgsNormalLibraryId": wgs_normal_library_id,
        "wtsTumorFastqListRowIds": wts_tumor_fastq_list_row_ids,
        "wgsTumorFastqListRowIds": wgs_tumor_fastq_list_row_ids,
        "wgsNormalFastqListRowIds": wgs_normal_fastq_list_row_ids,
    }

    return {
        "input_event_data": input_event_data,
        "event_tags": event_tags
    }
