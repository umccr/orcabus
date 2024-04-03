#!/usr/bin/env python

"""
The launch CWL pipeline expects the following as inputs

{
  "project_id": "project_id",
  "user_reference": "user_reference",
  "bclconvert_report_directory": "icav2://project_id/path/to/run/folder/report/",
  "interop_directory": "icav2://project_id/path/to/interop/directory",
  "run_id": "run_id",
  "analysis_output_uri": "icav2://project_id/path/to/out/",
  "technical_tags": {
      "portal_run_id": "string",
      "step_execution_arn": "string",
      "step_functions_inputs": "string"
  },
  "user_tags": {
    "instrument_run_id": "string"
  },
}

With the following environment variables

ICAV2_ACCESS_TOKEN_SECRET_ID

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
    ICAv2CwlAnalysisJsonInput,
    ICAv2CWLPipelineAnalysis,
    ICAv2PipelineAnalysisTags
)
from wrapica.libica_models import Analysis
from wrapica.utils import recursively_build_open_api_body_from_libica_item

from bclconvert_interop_qc_pipeline_manager_tools.utils.ssm_helpers import (
    set_icav2_env_vars,
    get_interop_qc_pipeline_id_from_ssm
)

# Globals




def handler(event, context):
    # Set icav2 environment variables
    set_icav2_env_vars()

    # Get inputs
    project_id = event.get("project_id", None)
    user_reference = event.get("user_reference", None)
    bclconvert_report_directory = event.get("bclconvert_report_directory", None)
    interop_directory = event.get("interop_directory", None)
    run_id = event.get("run_id", None)
    analysis_output_uri = event.get("analysis_output_uri", None)

    # Get technical tags
    technical_tags = event.get("technical_tags", {})

    # Get user tags
    user_tags = event.get("user_tags", {})

    # Get the pipeline urn from SSM
    pipeline_id = get_interop_qc_pipeline_id_from_ssm()

    # Check inputs

    # Check project id
    if not project_id:
        raise ValueError("project_id is required")

    # Check user reference
    if not user_reference:
        raise ValueError("user_reference is required")

    if not bclconvert_report_directory:
        raise ValueError("bclconvert_report_directory is required")
    if not interop_directory:
        raise ValueError("interop_directory is required")
    if not run_id:
        raise ValueError("run_id is required")

    # Check analysis output uri
    if not analysis_output_uri:
        raise ValueError("analysis_output_uri is required")

    # Get samplesheet uri from data id
    icav2_cwl_analysis_input_obj = ICAv2CwlAnalysisJsonInput(
        input_json={
            "bclconvert_report_directory": {
                "class": "Directory",
                "location": f"{bclconvert_report_directory}"
            },
            "interop_directory": {
                "class": "Directory",
                "location": f"{interop_directory}"
            },
            "run_id": run_id
        }
    )

    # Initialise an ICAv2CWLPipeline Analysis object
    cwl_analysis = ICAv2CWLPipelineAnalysis(
        user_reference=user_reference,
        project_id=project_id,
        pipeline_id=pipeline_id,
        analysis_input=icav2_cwl_analysis_input_obj.create_analysis_input(),
        analysis_output_uri=analysis_output_uri,
        tags=ICAv2PipelineAnalysisTags(
            technical_tags=technical_tags,
            user_tags=user_tags,
            reference_tags=[]
        )
    )

    # Generate the inputs and analysis object
    # Call the object to launch it
    analysis_launch_obj: Analysis = cwl_analysis()

    # Save the analysis
    with NamedTemporaryFile(suffix='.json') as temp_file:
        cwl_analysis.save_analysis(Path(temp_file.name))

        with open(Path(temp_file.name), 'r') as tmp_file_h:
            analysis_launch_payload = json.load(tmp_file_h)

    return {
        "analysis_id": analysis_launch_obj.id,
        "analysis_status": analysis_launch_obj.status,
        "analysis_return_payload": recursively_build_open_api_body_from_libica_item(analysis_launch_obj),
        "analysis_launch_payload": analysis_launch_payload
    }


# if __name__ == "__main__":
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2Jwticav2-credentials-umccr-service-user-trial"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "user_tags": {
#                         "instrument_run_id": "231116_A01052_0172_BHVLM5DSX7"
#                     },
#                     "technical_tags": {
#                         "portal_run_id": "20240403abcd1234"
#                     },
#                     "run_id": "231116_A01052_0172_BHVLM5DSX7",
#                     "user_reference": "umccr_trial__orcabus_semi_automated__bclconvert_qc_pipeline__20240403abcd1234",
#                     "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                     "bclconvert_report_directory": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Reports/",
#                     "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/bclconvert_interop-qc/1_3_1__1_21__20240312031410/20240403abcd1234/",
#                     "interop_directory": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/InterOp/"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )
