#!/usr/bin/env python

"""
The launch CWL pipeline expects the following as inputs

{
  "project_id": "project_id",
  "pipeline_id": "pipeline_id",
  "user_reference": "user_reference",
  "input_json": "{
    "bclconvert_report_directory": {
      "class": "File",
      "location": "icav2://project_id/path/to/run/folder/report/"
    }
    "interop_directory": {
      "class": "Directory",
      "location": "icav2://project_id/path/to/interop/directory"
    }
    "run_id": "run_id",
  }",
  "ica_logs_uri": "icav2://project_id/path/to/logs/",
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
from os import environ
import typing
import boto3

# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

# Imports
from wrapica.project_pipelines import (
    ICAv2PipelineAnalysisTags
)
from wrapica.libica_models import Analysis
from wrapica.utils import recursively_build_open_api_body_from_libica_item


# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Functions
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def handler(event, context):
    # Set icav2 environment variables
    set_icav2_env_vars()

    # Get inputs
    project_id = event.get("project_id", None)
    user_reference = event.get("user_reference", None)
    input_json = json.loads(event.get("input_json", {}))

    # Get the output uris
    analysis_output_uri = event.get("analysis_output_uri", None)
    ica_logs_uri = event.get("ica_logs_uri", None)

    # Get technical tags
    technical_tags = event.get("technical_tags", {})

    # Get user tags
    user_tags = event.get("user_tags", {})

    # Get the pipeline id
    pipeline_id = event.get("pipeline_id")

    # Get the workflow type
    workflow_type = event.get("workflow_type", None)

    # Check project id
    if not project_id:
        raise ValueError("project_id is required")

    # Check user reference
    if not user_reference:
        raise ValueError("user_reference is required")

    # Check analysis output uri
    if not analysis_output_uri:
        raise ValueError("analysis_output_uri is required")
    if not ica_logs_uri:
        raise ValueError("ica_logs_uri is required")

    # Check workflow type
    if workflow_type is None:
        raise ValueError(f"workflow_type should be one of 'nextflow' or 'cwl', got {workflow_type} instead")

    if workflow_type.lower() == 'cwl':
        from wrapica.project_pipelines import (
            ICAv2CwlAnalysisJsonInput as ICAv2AnalysisInput,
            ICAv2CWLPipelineAnalysis as ICAv2PipelineAnalysis,
        )
        # Collect the input json
        icav2_analysis_input_obj = ICAv2AnalysisInput(
            input_json=input_json
        )
    elif workflow_type.lower() == 'nextflow':
        from wrapica.project_pipelines import (
            ICAv2NextflowAnalysisInput as ICAv2AnalysisInput,
            ICAv2NextflowPipelineAnalysis as ICAv2PipelineAnalysis,
        )
        # Collect the input json
        icav2_analysis_input_obj = ICAv2AnalysisInput(
            input_json=input_json,
            project_id=project_id,
            pipeline_id=pipeline_id
        )
    else:
        raise ValueError(f"workflow_type should be one of 'nextflow' or 'cwl' got {workflow_type} instead")

    # Initialise an ICAv2CWLPipeline Analysis object
    analysis_obj = ICAv2PipelineAnalysis(
        user_reference=user_reference,
        project_id=project_id,
        pipeline_id=pipeline_id,
        analysis_input=icav2_analysis_input_obj.create_analysis_input(),
        analysis_output_uri=analysis_output_uri,
        ica_logs_uri=ica_logs_uri,
        tags=ICAv2PipelineAnalysisTags(
            technical_tags=technical_tags,
            user_tags=user_tags,
            reference_tags=[]
        )
    )

    # Generate the inputs and analysis object
    # Call the object to launch it
    analysis_launch_obj: Analysis = analysis_obj()

    # Save the analysis
    with NamedTemporaryFile(suffix='.json') as temp_file:
        analysis_obj.save_analysis(Path(temp_file.name))

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
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-trial"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                   "workflow_type": "cwl",
#                   "user_tags": {
#                     "projectname": "trial"
#                   },
#                   "technical_tags": {
#                     "portal_run_id": "20240510abcd0015",
#                     "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:aace90a0-37a2-c82f-e176-14008dccaff0_eab7d881-f6bc-a492-1cc2-c23fbcea8ea4"
#                   },
#                   "user_reference": "bclconvert_interop__semi_automated__umccr__pipeline",
#                   "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                   "pipeline_id": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
#                   "ica_logs_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0015/logs/",
#                   "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240510abcd0015/out/",
#                   "input_json": "{\"bclconvert_report_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Reports/\"},\"interop_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/InterOp/\"},\"run_id\":\"231116_A01052_0172_BHVLM5DSX7\"}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )
