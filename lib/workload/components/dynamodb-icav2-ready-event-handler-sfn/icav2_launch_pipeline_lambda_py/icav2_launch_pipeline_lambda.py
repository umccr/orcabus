#!/usr/bin/env python

"""
The launch CWL pipeline expects the following as inputs

{
    "workflow_type": "cwl",
    "user_tags": {
        "projectname": "trial"
    },
    "technical_tags": {
        "portal_run_id": "20240512abcd1234",
        "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:79ac2500-24ec-793f-81b3-50439944a235_92f04a8c-4f36-1594-ae52-cde6930f621e"
    },
    "user_reference": "bclconvert_interop__semi_automated__umccr__pipeline",
    "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
    "pipeline_id": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
    "ica_logs_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240512abcd1234/logs/",
    "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240512abcd1234/out/",
    "input_json": "{\"bclconvert_report_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Reports/\"},\"interop_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/InterOp/\"},\"run_id\":\"231116_A01052_0172_BHVLM5DSX7\"}"
}

With the following environment variables

ICAV2_ACCESS_TOKEN_SECRET_ID

The lambda then returns the following
{
  "analysis_id": "f2b9e6ab-1c3c-467e-9b5c-8c232ed26a1b",
  "analysis_status": "REQUESTED",
  "analysis_return_payload": {
    "id": "f2b9e6ab-1c3c-467e-9b5c-8c232ed26a1b",
    "timeCreated": "2024-05-12T23:57:25Z",
    "timeModified": "2024-05-12T23:57:26Z",
    "owner": {
      "id": "a9938581-7bf5-35d2-b461-282f34794dd1"
    },
    "tenant": {
      "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
      "name": "umccr-prod"
    },
    "reference": "bclconvert_interop__semi_automated__umccr__pipeline-bclconvert-interop-qc__1_3_1--1_21__20240313015132-1a823307-c69c-4b18-8e8b-19bc1ee196ab",
    "userReference": "bclconvert_interop__semi_automated__umccr__pipeline",
    "pipeline": {
      "id": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
      "timeCreated": "2024-03-13T01:53:51Z",
      "timeModified": "2024-03-13T01:53:51Z",
      "owner": {
        "id": "a9938581-7bf5-35d2-b461-282f34794dd1"
      },
      "tenant": {
        "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
        "name": "umccr-prod"
      },
      "code": "bclconvert-interop-qc__1_3_1--1_21__20240313015132",
      "description": "GitHub Release URL: https://github.com/umccr/cwl-ica/releases/tag/bclconvert-interop-qc/1.3.1--1.21__20240313015132",
      "language": "CWL",
      "pipelineTags": {
        "technicalTags": []
      },
      "analysisStorage": {
        "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
        "name": "Small",
        "description": "1.2TB"
      },
      "urn": "urn:ilmn:ica:pipeline:f606f580-d476-47a8-9679-9ddb39fcb0a8#bclconvert-interop-qc__1_3_1--1_21__20240313015132",
      "proprietary": false
    },
    "status": "REQUESTED",
    "tags": {
      "technicalTags": [
        "portal_run_id=20240512abcd1234",
        "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:79ac2500-24ec-793f-81b3-50439944a235_92f04a8c-4f36-1594-ae52-cde6930f621e"
      ],
      "userTags": [
        "projectname=trial"
      ],
      "referenceTags": []
    },
    "analysisStorage": {
      "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
      "name": "Small",
      "description": "1.2TB"
    },
    "analysisPriority": "LOW"
  },
  "analysis_launch_payload": {
    "userReference": "bclconvert_interop__semi_automated__umccr__pipeline",
    "pipelineId": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
    "tags": {
      "technicalTags": [
        "portal_run_id=20240512abcd1234",
        "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:79ac2500-24ec-793f-81b3-50439944a235_92f04a8c-4f36-1594-ae52-cde6930f621e"
      ],
      "userTags": [
        "projectname=trial"
      ],
      "referenceTags": []
    },
    "analysisInput": {
      "objectType": "JSON",
      "inputJson": "{\n  \"bclconvert_report_directory\": {\n    \"class\": \"Directory\",\n    \"location\": \"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.81ad1cb41b92470d530608dc3cf57419/Reports\"\n  },\n  \"interop_directory\": {\n    \"class\": \"Directory\",\n    \"location\": \"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.454782a16e9342b9e4e808dc388cff32/InterOp\"\n  },\n  \"run_id\": \"231116_A01052_0172_BHVLM5DSX7\"\n}",
      "mounts": [
        {
          "dataId": "fol.81ad1cb41b92470d530608dc3cf57419",
          "mountPath": "7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.81ad1cb41b92470d530608dc3cf57419/Reports"
        },
        {
          "dataId": "fol.454782a16e9342b9e4e808dc388cff32",
          "mountPath": "7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.454782a16e9342b9e4e808dc388cff32/InterOp"
        }
      ],
      "externalData": [],
      "dataIds": [
        "fol.81ad1cb41b92470d530608dc3cf57419",
        "fol.454782a16e9342b9e4e808dc388cff32"
      ]
    },
    "activationCodeDetailId": "103094d2-e932-4e34-8dd4-06ee1fb8be68",
    "analysisStorageId": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
    "outputParentFolderId": null,
    "analysisOutput": [
      {
        "sourcePath": "out/",
        "targetProjectId": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
        "targetPath": "/interop_qc/20240512abcd1234/out/",
        "type": "FOLDER"
      }
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
#                     "workflow_type": "cwl",
#                     "user_tags": {
#                         "projectname": "trial"
#                     },
#                     "technical_tags": {
#                         "portal_run_id": "20240512abcd1234",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:79ac2500-24ec-793f-81b3-50439944a235_92f04a8c-4f36-1594-ae52-cde6930f621e"
#                     },
#                     "user_reference": "bclconvert_interop__semi_automated__umccr__pipeline",
#                     "project_id": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
#                     "pipeline_id": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
#                     "ica_logs_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240512abcd1234/logs/",
#                     "analysis_output_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/interop_qc/20240512abcd1234/out/",
#                     "input_json": "{\"bclconvert_report_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Reports/\"},\"interop_directory\":{\"class\":\"Directory\",\"location\":\"icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/InterOp/\"},\"run_id\":\"231116_A01052_0172_BHVLM5DSX7\"}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )
