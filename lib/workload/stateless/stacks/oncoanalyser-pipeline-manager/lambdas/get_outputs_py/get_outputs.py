#!/usr/bin/env python3

"""
Given the engine parameters and inputs, use these to collect the output uris

For oncoanalyser-wgts-dna:
    * Extend the outputUri from the engineParameters with the tumorSampleId and normalSampleId

For oncoanalyser-wgts-rna:
    * Extend the outputUri from the engineParameters with the tumorSampleId
"""

# Imports
from pathlib import Path
from urllib.parse import urlparse, urlunparse


# Functions
def extend_url(url, path_ext: str) -> str:
    """
    Extend the url path with the path_ext
    """
    url_obj = urlparse(url)

    return str(
        urlunparse(
            (
                url_obj.scheme,
                url_obj.netloc,
                str(Path(url_obj.path) / path_ext),
                url_obj.params,
                url_obj.query,
                url_obj.fragment
            )
        )
    )


def handler(event, context):
    """
    Map the status of the job to the nextflow status
    """

    # Get the inputs and engine parameters from the event
    workflow_name = event.get('workflow_name')
    inputs = event.get('inputs', {})
    engine_parameters = event.get('engine_parameters', {})

    # Get the output uri from the engine parameters
    output_uri = engine_parameters.get('outputUri')

    # If the output uri is not set, return an empty dict
    if not output_uri:
        return {}

    # If the output uri is set, then we need to extend the output uri with the tumor and normal sample ids
    if workflow_name == "oncoanalyser-wgts-dna":

        # Get the tumor and normal sample ids
        tumor_sample_id = inputs.get('tumorDnaSampleId')
        normal_sample_id = inputs.get('normalDnaSampleId')
        return {
            "outputs": {
                "dnaOncoanalyserAnalysisUri": extend_url(output_uri, f'{tumor_sample_id}_{normal_sample_id}') + '/'
            }
        }
    elif workflow_name == "oncoanalyser-wgts-rna":
        tumor_sample_id = inputs.get('tumorRnaSampleId')
        return {
            "outputs": {
                "rnaOncoanalyserAnalysisUri": extend_url(output_uri, f'{tumor_sample_id}') + '/'
            }
        }
    elif workflow_name == "oncoanalyser-wgts-dna-rna":
        tumor_dna_sample_id = inputs.get('tumorDnaSampleId')
        normal_dna_sample_id = inputs.get('normalDnaSampleId')
        tumor_rna_sample_id = inputs.get('tumorRnaSampleId')
        return {
            "outputs": {
                "oncoanalyserAnalysisUri": extend_url(output_uri, f'{tumor_dna_sample_id}_{normal_dna_sample_id}_{tumor_rna_sample_id}') + '/'
            }
        }
    else:
        return {}