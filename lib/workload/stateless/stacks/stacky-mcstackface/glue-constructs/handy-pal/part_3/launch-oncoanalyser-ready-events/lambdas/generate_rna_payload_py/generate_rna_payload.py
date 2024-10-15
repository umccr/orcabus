#!/usr/bin/env python3

"""
Generate draft event payload for the event

Given the tumor library id and normal library id, generate the inputs for the workflow.

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysis_type": "DNA | RNA | DNA/RNA"
     "subject_id": "<subject_id>", // Required
     "tumor_rna_sample_id": "<rna_sample_id>",  // Required if analysis_type is set to RNA
     "tumor_rna_fastq_uri_list": [ <Array of wts fastq list rows> ]  // Required if analysis_type is set to RNA
   },
   "tags": {
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

"""

# GLOBALS
MODE = "wgts"
ANALYSIS_TYPE = "RNA"

# Functions
from typing import Dict, List
from more_itertools import flatten


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """

    tumor_library_id = event['tumor_library_id']
    subject_id = event['subject_id']
    individual_id = event['individual_id']
    tumor_fastq_list_rows: List[Dict] = event['tumor_fastq_list_rows']
    tumor_fastq_list_row_ids: List[str] = event['tumor_fastq_list_row_ids']

    return {
        "input_event_data": {
            "mode": MODE,
            "analysisType": ANALYSIS_TYPE,
            "subjectId": subject_id,
            "tumorRnaSampleId": tumor_library_id,
            "tumorRnaFastqUriList": flatten(list(map(lambda fastq_list_row_iter_: [fastq_list_row_iter_.get("read1FileUri"), fastq_list_row_iter_.get("read2FileUri")], tumor_fastq_list_rows))),
        },
        "event_tags": {
            "subjectId": subject_id,
            "tumorLibraryId": tumor_library_id,
            "tumorFastqListRowIds": tumor_fastq_list_row_ids,
        }
    }
