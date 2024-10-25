#!/usr/bin/env python3

"""
Generate a payload for the sash event

   "inputs": {
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
                url_obj.scheme,
                url_obj.netloc,
                str(url_path),
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
    oncoanalyser_dna_s3_uri = event['oncoanalyser_dna_s3_uri']

    # Tags specific inputs
    subject_id = event['subject_id']
    individual_id = event['individual_id']

    # Get the bam uris by taking the library ids
    return {
        "input_event_data": {
            "subjectId": subject_id,
            "tumorDnaSampleId": tumor_library_id,
            "normalDnaSampleId": normal_library_id,
            "dragenSomaticUri": dragen_somatic_output_s3_uri,
            "dragenGermlineUri": dragen_germline_output_s3_uri,
            "oncoanalyserDnaUri": oncoanalyser_dna_s3_uri,
        },
        "event_tags": {
            "subjectId": subject_id,
            "individualId": individual_id,
            "tumorLibraryId": tumor_library_id,
            "normalLibraryId": normal_library_id
        }
    }
