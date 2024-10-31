#!/usr/bin/env python3

"""
Generate the dna/rna inputs payload for the nextflow stack

Inputs: {
    "mode": "wgts",
    "analysisType": "DNA/RNA",
    "subjectId": subject_id,
    "tumorDnaSampleId": tumor_dna_library_id,
    "normalDnaSampleId": normal_dna_library_id,
    "tumorRnaSampleId": tumor_rna_library_id,
    "dnaOncoanalyserAnalysisUri": dna_oncoanalyser_analysis_uri,
    "rnaOncoanalyserAnalysisUri": dna_oncoanalyser_analysis_uri,
}

Tags: {
    "tumorDnaLibraryId": tumor_dna_library_id,
    "normalDnaLibraryId": normal_dna_library_id,
    "tumorRnaLibraryId": tumor_rna_library_id,
    "subjectId": subject_id,
    "individualId": individual_id,
}
"""

# GLOBALS
MODE = "wgts"
ANALYSIS_TYPE = "DNA/RNA"

# Functions
from typing import Dict


def handler(event, context) -> Dict:
    """
    Generate draft event payload for the event
    """

    # Inputs
    subject_id = event['subject_id']
    individual_id = event['individual_id']
    tumor_dna_library_id = event['tumor_dna_library_id']
    normal_dna_library_id = event['normal_dna_library_id']
    tumor_rna_library_id = event['tumor_rna_library_id']
    dna_outputs = event['dna_outputs']
    rna_outputs = event['rna_outputs']

    return {
        "input_event_data": {
            "mode": MODE,
            "analysisType": ANALYSIS_TYPE,
            "subjectId": subject_id,
            "tumorDnaSampleId": tumor_dna_library_id,
            "normalDnaSampleId": normal_dna_library_id,
            "tumorRnaSampleId": tumor_rna_library_id,
            "dnaOncoanalyserAnalysisUri": dna_outputs.get("dnaOncoanalyserAnalysisUri"),
            "rnaOncoanalyserAnalysisUri": rna_outputs.get("rnaOncoanalyserAnalysisUri"),
        },
        "event_tags": {
            "tumorDnaLibraryId": tumor_dna_library_id,
            "normalDnaLibraryId": normal_dna_library_id,
            "tumorRnaLibraryId": tumor_rna_library_id,
            "subjectId": subject_id,
            "individualId": individual_id,
        }
    }


