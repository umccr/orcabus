#!/usr/bin/env python3

"""
Given a
* library id,
* sample type,
* fastq list row
* fastq list row id

Generate a wgts draft event

This will have the following properties:

outputFilePrefix
outputDirectoryName
referenceVersion
sampleType
fastqListRowId
fastqListRow

Plus

gencodeAnnotationVersion if the sampleType is 'WTS'

Mapping is as follows

outputFilePrefix = library_id
outputDirectoryName = library_id
referenceVersion = 'v9-r3'  # The default version
sampleType = sample_type (one of WTS or WGS)
fastqListRowId = fastq_list_row_id
fastqListRow = fastq_list_row

If the sampleType is WTS, then the gencodeAnnotationVersion is 'v39'
"""

# GLOBALS #
DEFAULT_DRAGEN_REFERENCE_VERSION = "v9-r3"
DEFAULT_GENCODE_ANNOTATION_VERSION = "v39"


def handler(event, context):
    """
    Convert the inputs into a draft event
    :param event:
    :param context:
    :return:
    """
    # Get input values
    library_id = event['library_id']
    sample_type = event['sample_type']
    fastq_list_row = event['fastq_list_row']
    fastq_list_row_id = event['fastq_list_row_id']

    # Generate the draft event
    draft_event = {
        'outputFilePrefix': library_id,
        'outputDirectoryName': library_id,
        'referenceVersion': DEFAULT_DRAGEN_REFERENCE_VERSION,
        'sampleType': sample_type,
        'fastqListRowId': fastq_list_row_id,
        'fastqListRow': fastq_list_row
    }

    if sample_type.lower() == 'wts':
        draft_event['gencodeAnnotationVersion'] = DEFAULT_GENCODE_ANNOTATION_VERSION

    return {
        "event_output_dict": draft_event
    }
