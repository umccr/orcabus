#!/usr/bin/env python3

"""
Generate the payload for the sash stack
"""


# Imports
import json


# Globals
WORKFLOW_NAME = "sash"

NEXTFLOW_TAGS = {
    "Stack": "NextflowStack",
    "SubStack": "SashStack",
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
    tags['PortalRunId'] = event.get("portal_run_id")

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

    # Add portal run id to engine parameters
    engine_parameters.update(
        {
            "portal_run_id": event.get("portal_run_id")
        }
    )

    # Pop the pipeline version from engine_parameters
    pipeline_version = engine_parameters.pop('pipeline_version', event.get('default_pipeline_version'))

    # Generate the payload
    return {
        "overrides": {
            "resource_requirements": [
                {
                    "Type": "MEMORY", "Value": "15000"
                },
                {
                    "Type": "VCPU", "Value": "2"
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
            "workflow": WORKFLOW_NAME,
            "version": pipeline_version,
            "output": json.dumps(
                {
                    "output_directory": engine_parameters.get("output_results_dir")
                },
                separators=(',', ':')
            ),
            "orcabus": "true",
        },
        "tags": tags
    }
