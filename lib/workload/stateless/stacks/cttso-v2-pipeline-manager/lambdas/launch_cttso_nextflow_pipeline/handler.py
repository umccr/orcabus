#!/usr/bin/env python

"""
The launch nextflow pipeline expects the following as inputs

{
  "project_id": "project_id",
  "user_reference": "user_reference",
  "run_folder_uri": "icav2://project_id/path/to/run/folder/",
  "samplesheet_uri": "icav2://project_id/path/to/samplesheet",
  "sample_id": "sample_id",
  "analysis_output_uri": "icav2://project_id/path/to/out/",
  "technical_tags": {
      "portal_run_id": "string",
      "step_execution_arn": "string",
      "step_functions_inputs": "string"
  },
  "user_tags": {
    "subject_id": "string",
    "library_id": "string",
    "project_name": "string",
    "project_owner": "string",
    "instrument_run_id": "string"
  },
}

The analysis pipeline then returns the following

{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "timeCreated": "2024-02-15T22:28:01.487Z",
  "timeModified": "2024-02-15T22:28:01.487Z",
  "ownerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "tenantId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "tenantName": "string",
  "reference": "string",
  "userReference": "string",
  "pipeline": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "timeCreated": "2024-02-15T22:28:01.487Z",
    "timeModified": "2024-02-15T22:28:01.487Z",
    "ownerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "tenantId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "tenantName": "string",
    "code": "string",
    "urn": "string",
    "description": "string",
    "language": "Nextflow",
    "languageVersion": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "language": "Nextflow"
    },
    "pipelineTags": {
      "technicalTags": [
        "string"
      ]
    },
    "analysisStorage": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "timeCreated": "2024-02-15T22:28:01.487Z",
      "timeModified": "2024-02-15T22:28:01.487Z",
      "ownerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "tenantId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "tenantName": "string",
      "name": "string",
      "description": "string"
    },
    "proprietary": false
  },
  "status": "REQUESTED",
  "startDate": "2024-02-15T22:28:01.487Z",
  "endDate": "2024-02-15T22:28:01.487Z",
  "summary": "string",
  "analysisStorage": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "timeCreated": "2024-02-15T22:28:01.487Z",
    "timeModified": "2024-02-15T22:28:01.487Z",
    "ownerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "tenantId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "tenantName": "string",
    "name": "string",
    "description": "string"
  },
  "analysisPriority": "LOW",
  "tags": {
    "technicalTags": [
      "portal_run_id=string",
      "step_execution_arn=string",
      "step_functions_inputs=string"
    ],
    "userTags": [
      "subject_id=string",
      "library_id=string",
      "project_name=string",
      "project_owner=string",
      "instrument_run_id=string"
    ],
    "referenceTags": [
      "string"
    ]
  }
}
"""
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

# Imports
from wrapica.project_pipelines import (
    ICAv2NextflowAnalysisInput,
    ICAv2NextflowPipelineAnalysis,
    ICAv2PipelineAnalysisTags
)
from wrapica.libica_models import Analysis
from wrapica.utils import recursively_build_open_api_body_from_libica_item

from cttso_v2_pipeline_manager_tools.utils.aws_ssm_helpers import get_tso500_ctdna_2_1_pipeline_id_from_ssm
from cttso_v2_pipeline_manager_tools.utils.aws_ssm_helpers import set_icav2_env_vars


# Globals


def handler(event, context):
    # Set icav2 environment variables
    set_icav2_env_vars()

    # Get inputs
    project_id = event.get("project_id", None)
    user_reference = event.get("user_reference", None)
    run_folder_uri = event.get("run_folder_uri", None)
    samplesheet_uri = event.get("samplesheet_uri", None)
    sample_id = event.get("sample_id", None)
    analysis_output_uri = event.get("analysis_output_uri", None)

    # Get technical tags
    technical_tags = event.get("technical_tags", {})

    # Get user tags
    user_tags = event.get("user_tags", {})

    # Get the pipeline urn from SSM
    pipeline_id = get_tso500_ctdna_2_1_pipeline_id_from_ssm()

    # Check inputs

    # Check project id
    if not project_id:
        raise ValueError("project_id is required")

    # Check user reference
    if not user_reference:
        raise ValueError("user_reference is required")

    # Check run folder uri
    if not run_folder_uri:
        raise ValueError("run_folder_uri is required")

    # Check samplesheet uri
    if not samplesheet_uri:
        raise ValueError("samplesheet_uri is required")

    # Check sample id
    if not sample_id:
        raise ValueError("sample_id is required")

    # Check analysis output uri
    if not analysis_output_uri:
        raise ValueError("analysis_output_uri is required")

    # Get samplesheet uri from data id
    icav2_nextflow_analysis_input_obj = ICAv2NextflowAnalysisInput(
        project_id=project_id,
        pipeline_id=pipeline_id,
        input_json={
            "run_folder": run_folder_uri,
            "sample_sheet": samplesheet_uri,
            "StartsFromFastq": 'true',
            "sample_pair_ids": [
                sample_id
            ]
        }
    )

    # Initialise an ICAv2CWLPipeline Analysis object
    nextflow_analysis = ICAv2NextflowPipelineAnalysis(
        user_reference=user_reference,
        project_id=project_id,
        pipeline_id=pipeline_id,
        analysis_input=icav2_nextflow_analysis_input_obj.create_analysis_input(),
        analysis_output_uri=analysis_output_uri,
        tags=ICAv2PipelineAnalysisTags(
            technical_tags=technical_tags,
            user_tags=user_tags,
            reference_tags=[]
        )
    )

    # Generate the inputs and analysis object
    # Call the object to launch it
    analysis_launch_obj: Analysis = nextflow_analysis()

    # Save the analysis
    with NamedTemporaryFile(suffix='.json') as temp_file:
        nextflow_analysis.save_analysis(Path(temp_file.name))

        with open(Path(temp_file.name), 'r') as tmp_file_h:
            analysis_launch_payload = json.load(tmp_file_h)

    return {
        "analysis_id": analysis_launch_obj.id,
        "analysis_return_payload": recursively_build_open_api_body_from_libica_item(analysis_launch_obj),
        "analysis_launch_payload": analysis_launch_payload,
        "analysis_status": analysis_launch_obj.status
    }


if __name__ == "__main__":
    print(
        json.dumps(
            handler(
                event={
                    "user_tags": {
                        "subject_id": "SBJ04405",
                        "library_id": "L2301368",
                        "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7",
                        "project_owner": "UMCCR",
                        "project_name": "testing"
                    },
                    "technical_tags": {
                        "portal_run_id": "20240308abcd1234",
                        "step_functions_execution_arn": "$$.Execution.id"
                    },
                    "user_reference": "PTC-ctTSO-v2-launch-test",
                    "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
                    "samplesheet_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240308abcd1234/L2301368_run_cache/SampleSheet.csv",
                    "sample_id": "L2301368",
                    "run_folder_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240308abcd1234/L2301368_run_cache/",
                    "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_cttso_fastq_cache/20240308abcd1234/"
                },
                context=None
            ),
            indent=2
        )
    )
