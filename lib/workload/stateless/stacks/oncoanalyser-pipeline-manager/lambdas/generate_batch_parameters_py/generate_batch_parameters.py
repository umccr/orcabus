#!/usr/bin/env python3

"""
Generate the payload for the nextflow lambda stack

We have three different payloads to generate depending on the workflow type,
but all have the following schema

{
   "inputs": {
     "mode": "wgts | targeted"
     "analysis_type": "DNA | RNA | DNA/RNA"
     "subject_id": "<subject_id>", // Required
     "tumor_dna_sample_id": "<tumor_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "normal_dna_sample_id": "<normal_sample_id>",  // Required if analysis_type is set to DNA or DNA/RNA
     "tumor_dna_bam_uri": "<tumor_bam_uri>",  // Required if analysis_type is set to DNA
     "normal_dna_bam_uri": "<normal_bam_uri>",  // Required if analysis_type is set to DNA
     "tumor_rna_sample_id": "<rna_sample_id>",  // Required if analysis_type is set to RNA
     "tumor_rna_fastq_uri_list": [ <Array of wts fastq list rows> ]  // Required if analysis_type is set to RNA
     "dna_oncoanalyser_analysis_uri": "<oncoanalyser_dir>"  // Required if analysis_type is set to DNA/RNA
     "rna_oncoanalyser_analysis_uri": "<oncoanalyser_dir>"  // Required if analysis_type is set to DNA/RNA
   },
   "engine_parameters": {
     "portal_run_id": "<portal_run_id>",  // Always required
     "output_results_dir": "<output_results_dir>",  // Always required
     "output_staging_dir": "<output_staging_dir>",  // Always required
     "output_scratch_dir": "<output_scratch_dir>",  // Always required
     "custom_config_str":  "<custom_config_str>"  // Optional
     "resume_nextflow_uri": "<resume_nextflow_uri>"  // Optional
     "pipeline_version": "<pipeline_version>"  // Optional
   },
   "tags": {
      "tumorDnaLibraryId": "<tumor_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "normalDnaLibraryId": "<normal_sample_id>", // Present if analysis_type is set to DNA or DNA/RNA
      "tumorRnaLibraryId": "<rna_sample_id>", // Present if analysis_type is set to RNA
      "subjectId": "<subject_id>",
      "individualId": "<individual_id>",
   }
}

Return the following payload
{
    "overrides": {
        "resource_requirements": [
            {
                "type": "MEMORY", "value": "15000"
            },
            {
                "type": "VCPU", "value": "2"
            }
        ]
        "command": ['./assets/run-v2.sh', '--manifest-json', '{"inputs":..., "engine_parameters": ...}',
    },
    "parameters": {
        "portal_run_id": '<portal_run_id>',
        "workflow": 'oncoanalyser_dna', // or oncoanalyser_rna or oncoanalyser_dna_rna
        "version": "<pipeline_version>",
        "output": "{"output_directory": "<output_results_dir>"}",
    },
    "tags": {
        "Stack": "NextflowStack",
        "SubStack": "OncoanalyserStack",
        "RunId": <portal_run_id>,
        "tumor_sample_id": "<tumor_sample_id>",
        "portal_run_id": "<portal_run_id>",
    }
}
"""


# Imports
import json


# Globals
ANALYSIS_TYPE_TO_WORKFLOW_MAPPER = {
    "DNA": "oncoanalyser-dna",
    "RNA": "oncoanalyser-rna",
    "DNA/RNA": "oncoanalyser-dna-rna"
}

NEXTFLOW_TAGS = {
    "Stack": "NextflowStack",
    "SubStack": "OncoanalyserStack",
}

ENGINE_PARAMETERS_MAPPER = {
    "output_uri": "output_results_dir",
    "cache_uri": "output_scratch_dir",
}


def camel_case_to_snake_case(name):
    """
    Convert camel case to snake case
    :param name:
    :return:
    """
    return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')


def handler(event, context):
    """
    Generate the payload for the nextflow lambda stack
    :param event:
    :param context:
    :return:
    """

    # Get inputs, engine_parameters and pipeline_version from event dict
    inputs = event.get('inputs', {})
    engine_parameters = event.get('engine_parameters', {})
    tags = event.get('tags', {})

    # Merge the tags
    tags.update(NEXTFLOW_TAGS)

    # Add the portal run id as a tag
    tags['PortalRunId'] = engine_parameters.get("portal_run_id")

    # Convert inputs and engine_parameters to snake case
    inputs = dict(map(
        lambda kv: (camel_case_to_snake_case(kv[0]), kv[1]),
        inputs.items()
    ))
    engine_parameters = dict(map(
        lambda kv: (camel_case_to_snake_case(kv[0]), kv[1]),
        engine_parameters.items()
    ))

    # Map engineparameters from wrsc to oncoanalyser
    engine_parameters = dict(map(
        lambda kv: (
            (ENGINE_PARAMETERS_MAPPER.get(kv[0], kv[0]), kv[1])
            if kv[0] in ENGINE_PARAMETERS_MAPPER
            else kv
        ),
        engine_parameters.items()
    ))


    # Pop the pipeline version from engine_parameters
    pipeline_version = engine_parameters.pop('pipeline_version', event.get('default_pipeline_version'))

    # Generate the payload
    return {
        "overrides": {
            "resource_requirements": [
                {
                    "type": "MEMORY", "value": "15000"
                },
                {
                    "type": "VCPU", "value": "2"
                }
            ],
            "command": [
                './assets/run-v2.sh',
                '--manifest-json', json.dumps(
                    {
                        "inputs": inputs,
                        "engine_parameters": engine_parameters
                    },
                    # Compact output
                    separators=(',', ':')
                ),
            ],
        },
        "parameters": {
            "portal_run_id": engine_parameters.get("portal_run_id"),
            "workflow": ANALYSIS_TYPE_TO_WORKFLOW_MAPPER.get(inputs.get("analysis_type")),
            "version": pipeline_version,
            "output": json.dumps(
                {
                    "output_directory": engine_parameters.get("output_results_dir")
                },
                separators=(',', ':')
            )
        },
        "tags": tags
    }
