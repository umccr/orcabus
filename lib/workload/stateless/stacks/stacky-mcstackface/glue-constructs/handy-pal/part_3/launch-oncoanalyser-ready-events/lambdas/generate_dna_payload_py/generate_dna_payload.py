#!/usr/bin/env python3

"""
Generate a DNA payload for the oncoanalyser event

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

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysisType": "DNA | RNA | DNA/RNA"
     "subjectId": "<subject_id>", // Required
     "tumorDnaSampleId": "<tumor_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "normalDnaSampleId": "<normal_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "tumorDnaBamUri": "<tumor_bam_uri>",  // Required if analysis_type is set to DNA
     "normalDnaBamUri": "<normal_bam_uri>",  // Required if analysis_type is set to DNA
   },
   "tags": {
      "tumorDnaLibraryId": "<tumor_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "normalDnaLibraryId": "<normal_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

"""

# GLOBALS
MODE = "wgts"
ANALYSIS_TYPE = "DNA"

# Functions
from typing import Dict, List
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def join_url_paths(url: str, path_ext: str) -> str:
    """
    Join the url paths
    :param url: str
    :param path_ext: str
    :return: url
    """
    url_obj = urlparse(url)
    url_path = Path(url_obj.path) / path_ext

    return str(
        urlunparse(
            (
                url_obj.netloc,
                url_obj.scheme,
                url_path,
                None, None, None
            )
        )
    )


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    :param event: event object
    :return: draft event payload
    """
    tumor_library_id = event['tumor_library_id']
    normal_library_id = event['normal_library_id']
    dragen_somatic_output_s3_uri = event['dragen_somatic_output_s3_uri']
    dragen_germline_output_s3_uri = event['dragen_germline_output_s3_uri']

    subject_id = event['subject_id']
    individual_id = event['individual_id']
    tumor_fastq_list_row_ids: List[str] = event['tumor_fastq_list_row_ids']
    normal_fastq_list_row_ids: List[str] = event['normal_fastq_list_row_ids']

    # Get the bam uris by taking the library ids


    return {
        "input_event_data": {
            "mode": MODE,
            "analysisType": ANALYSIS_TYPE,
            "subjectId": subject_id,
            "tumorDnaSampleId": tumor_library_id,
            "normalDnaSampleId": normal_library_id,
            "tumorDnaBamUri": join_url_paths(dragen_somatic_output_s3_uri, tumor_library_id + "_tumor.bam"),
            "normalDnaBamUri": join_url_paths(dragen_somatic_output_s3_uri, normal_library_id + "_normal.bam"),
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "tumorLibraryId": tumor_library_id,
            "normalLibraryId": normal_library_id,
            "tumorFastqListRowIds": tumor_fastq_list_row_ids,
            "normalFastqListRowIds": normal_fastq_list_row_ids,
            "dragenSomaticOutputS3Uri": dragen_somatic_output_s3_uri,
            "dragenGermlineOutputS3Uri": dragen_germline_output_s3_uri,
        }
    }
