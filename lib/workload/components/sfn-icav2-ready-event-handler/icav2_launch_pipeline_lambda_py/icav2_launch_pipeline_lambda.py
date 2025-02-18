#!/usr/bin/env python

"""
The launch CWL pipeline expects the following as inputs

{
    "workflow_type": "cwl",
    "user_tags": {
        "projectName": "trial"
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
from copy import copy
from pathlib import Path
from tempfile import NamedTemporaryFile
from os import environ
import typing
import boto3
import logging

from wrapica.enums import AnalysisStorageSize

# IDE imports only
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

# Imports
from wrapica.project_pipelines import (
    ICAv2PipelineAnalysisTags,
    get_analysis_storage_from_analysis_storage_size
)
from wrapica.libica_models import Analysis
from wrapica.utils import recursively_build_open_api_body_from_libica_item

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def camel_case_to_snake_case(camel_case_str: str) -> str:
    # Convert fastqListRowId to fastq_list_row_id
    return ''.join(['_' + i.lower() if i.isupper() else i for i in camel_case_str]).lstrip('_')


def handler(event, context):
    # Set icav2 environment variables
    logger.info("Setting ICAv2 Env Vars")
    set_icav2_env_vars()

    # Get inputs
    logger.info("Collecting lambda inputs")
    project_id = event.get("project_id", None)
    user_reference = event.get("user_reference", None)
    input_json = json.loads(event.get("input_json", {}))
    idempotency_key = event.get("idempotency_key", None)

    # Get the output uris
    analysis_output_uri = event.get("analysis_output_uri", None)
    ica_logs_uri = event.get("ica_logs_uri", None)

    # Get technical tags
    technical_tags = event.get("technical_tags", {})

    # Get user tags
    user_tags = event.get("user_tags", {})

    # Convert all user tag keys from camel case to snake case
    user_tags = dict(
        map(
            lambda kv: (camel_case_to_snake_case(kv[0]), kv[1]),
            user_tags.items()
        )
    )

    # Ensure if any user tags values are a list, these are flattened such that the key is
    # numerated with a '.iterable' extension
    # I.e
    # {
    #  "fastq_list_row_ids": ['index1.index2.lane1', 'index1.index2.lane2']
    # }
    # Becomes
    # {
    #  "fastq_list_row_ids.0": 'index1.index2.lane1',
    #  "fastq_list_row_ids.1": 'index1.index2.lane2'
    # }
    for key, value in copy(user_tags).items():
        if isinstance(value, list):
            for iter_, value_iter in enumerate(value):
                user_tags[f"{key}.{iter_}"] = value_iter
            del user_tags[key]

    # Get the analysis storage size
    analysis_storage_size: str = event.get("analysis_storage_size")

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
        logger.info("Collecting cwl inputs")
        icav2_analysis_input_obj = ICAv2AnalysisInput(
            input_json=input_json
        )
    elif workflow_type.lower() == 'nextflow':
        from wrapica.project_pipelines import (
            ICAv2NextflowAnalysisInput as ICAv2AnalysisInput,
            ICAv2NextflowPipelineAnalysis as ICAv2PipelineAnalysis,
        )
        # Collect the input json
        logger.info("Collecting nextflow inputs")
        icav2_analysis_input_obj = ICAv2AnalysisInput(
            input_json=input_json,
            project_id=project_id,
            pipeline_id=pipeline_id
        )
    else:
        raise ValueError(f"workflow_type should be one of 'nextflow' or 'cwl' got {workflow_type} instead")

    # Get the analysis storage size from the event
    # FIXME - need to directly use analysis storage size while
    # FIXME - https://github.com/umccr/wrapica/issues/115
    analysis_storage_size: AnalysisStorageSize = getattr(AnalysisStorageSize, event.get("analysis_storage_size"))

    # Initialise an ICAv2CWLPipeline Analysis object
    logger.info("Generating the analysis object")
    analysis_obj = ICAv2PipelineAnalysis(
        user_reference=user_reference,
        project_id=project_id,
        pipeline_id=pipeline_id,
        analysis_input=icav2_analysis_input_obj.create_analysis_input(),
        # FIXME - https://github.com/umccr/wrapica/issues/115
        analysis_storage_id=get_analysis_storage_from_analysis_storage_size(analysis_storage_size).id,
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
    logger.info("Launching the ICAv2 Analysis")
    analysis_launch_obj: Analysis = analysis_obj(
        idempotency_key=idempotency_key
    )

    # Save the analysis
    logger.info("Saving the analysis")
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


# CWL Test

# if __name__ == "__main__":
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
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


# # # Nextflow test
# if __name__ == "__main__":
#     import os
#
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "workflow_type": "nextflow",
#                     "user_tags": {},
#                     "technical_tags": {
#                         "portal_run_id": "20240714f428b64f",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:cttsov2Sfn-wfm-ready-event-handler:4e8f5a00-3a9d-e73d-77a5-1dedb119ac9d_bfd26923-adcc-5372-923a-ab74aa062c92",
#                         "analysis_output_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240714f428b64f/"
#                     },
#                     "user_reference": "umccr--automated--cttsov2--2-6-0--20240714f428b64f",
#                     "project_id": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#                     "pipeline_id": "c2dfdbaa-2074-44c7-8078-d33e13607061",
#                     "ica_logs_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/logs/cttsov2/20240714f428b64f/",
#                     "analysis_output_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/20240714f428b64f/",
#                     "input_json": "{\"StartsFromFastq\":true,\"sample_sheet\":\"icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20240714f428b64f/SampleSheet.csv\",\"run_folder\":\"icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20240714f428b64f/\",\"sample_pair_ids\":\"L2400166\"}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )
#
#     # {
#     #   "analysis_id": "12c25a8e-3afb-4fcf-b667-4321bf7c389a",
#     #   "analysis_status": "REQUESTED",
#     #   "analysis_return_payload": {
#     #     "id": "12c25a8e-3afb-4fcf-b667-4321bf7c389a",
#     #     "timeCreated": "2024-07-12T06:35:59Z",
#     #     "timeModified": "2024-07-12T06:36:02Z",
#     #     "owner": {
#     #       "id": "73636fd8-692b-375c-9081-d416cd6a4357"
#     #     },
#     #     "tenant": {
#     #       "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
#     #       "name": "umccr-prod"
#     #     },
#     #     "reference": "umccr--automated--cttsov2--2-5-0--202407121f5d45b0-TSO500 ctDNA v_2_5_0_24-52b3db6f-e8d9-4070-8960-89e52e73faba",
#     #     "userReference": "umccr--automated--cttsov2--2-5-0--202407121f5d45b0",
#     #     "pipeline": {
#     #       "id": "cb4bf1cf-b796-488c-8d88-e75fcb9336e1",
#     #       "timeCreated": "2023-11-09T23:49:26Z",
#     #       "timeModified": "2024-05-28T20:57:49Z",
#     #       "owner": {
#     #         "id": "ee171059-4283-3acb-b0b0-34d5b356be3f"
#     #       },
#     #       "tenant": {
#     #         "id": "25a4d4b2-ea16-4075-b09b-65ca3fee6d31",
#     #         "name": "ilmn-tso500"
#     #       },
#     #       "code": "TSO500 ctDNA v_2_5_0_24",
#     #       "description": "This is a TruSight Oncology 500 ctDNA pipeline using TSO500 ctDNA v_2_5_0_24.",
#     #       "language": "NEXTFLOW",
#     #       "pipelineTags": {
#     #         "technicalTags": []
#     #       },
#     #       "analysisStorage": {
#     #         "id": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
#     #         "name": "Large",
#     #         "description": "7.2TB"
#     #       },
#     #       "urn": "urn:ilmn:ica:pipeline:cb4bf1cf-b796-488c-8d88-e75fcb9336e1#TSO500_ctDNA_v_2_5_0_24",
#     #       "null": "RELEASED",
#     #       "languageVersion": {
#     #         "id": "b1585d18-f88c-4ca0-8d47-34f6c01eb6f3",
#     #         "name": "22.04.3",
#     #         "language": "NEXTFLOW"
#     #       },
#     #       "proprietary": true
#     #     },
#     #     "status": "REQUESTED",
#     #     "tags": {
#     #       "technicalTags": [
#     #         "portal_run_id=202407121f5d45b0",
#     #         "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:cttsov2Sfn-wfm-ready-event-handler:025ab108-907d-5a2d-1a89-dab51b32b633_8afebeb1-9355-83b5-e117-ef467881ad6c",
#     #         "analysis_output_uri=icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/202407121f5d45b0/"
#     #       ],
#     #       "userTags": [],
#     #       "referenceTags": []
#     #     },
#     #     "analysisStorage": {
#     #       "id": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
#     #       "name": "Large",
#     #       "description": "7.2TB"
#     #     },
#     #     "analysisPriority": "MEDIUM"
#     #   },
#     #   "analysis_launch_payload": {
#     #     "userReference": "umccr--automated--cttsov2--2-5-0--202407121f5d45b0",
#     #     "pipelineId": "cb4bf1cf-b796-488c-8d88-e75fcb9336e1",
#     #     "tags": {
#     #       "technicalTags": [
#     #         "portal_run_id=202407121f5d45b0",
#     #         "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:cttsov2Sfn-wfm-ready-event-handler:025ab108-907d-5a2d-1a89-dab51b32b633_8afebeb1-9355-83b5-e117-ef467881ad6c",
#     #         "analysis_output_uri=icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/cttsov2/202407121f5d45b0/"
#     #       ],
#     #       "userTags": [],
#     #       "referenceTags": []
#     #     },
#     #     "analysisInput": {
#     #       "inputs": [
#     #         {
#     #           "parameterCode": "sample_sheet",
#     #           "dataIds": [
#     #             "fil.53983ba4b38042212ccc08dc9b5404a7"
#     #           ]
#     #         },
#     #         {
#     #           "parameterCode": "run_folder",
#     #           "dataIds": [
#     #             "fol.ea5598ebd25645de2ccb08dc9b5404a7"
#     #           ]
#     #         }
#     #       ],
#     #       "parameters": [
#     #         {
#     #           "code": "StartsFromFastq",
#     #           "value": "True"
#     #         },
#     #         {
#     #           "code": "sample_pair_ids",
#     #           "multiValue": [
#     #             "L2400159"
#     #           ]
#     #         }
#     #       ]
#     #     },
#     #     "activationCodeDetailId": "103094d2-e932-4e34-8dd4-06ee1fb8be68",
#     #     "analysisStorageId": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
#     #     "analysisOutput": [
#     #       {
#     #         "sourcePath": "out/",
#     #         "targetProjectId": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#     #         "targetPath": "/analysis/cttsov2/202407121f5d45b0/",
#     #         "type": "FOLDER"
#     #       }
#     #     ]
#     #   }
#     # }


# # WGTS CWL Test
#
# if __name__ == "__main__":
#     import os
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "workflow_type": "cwl",
#                     "user_tags": {},
#                     "technical_tags": {
#                       "portal_run_id": "20240719dd1ffb82",
#                       "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:wgtsQcSfn-wfm-ready-event-handler:04ee188b-fd14-6a39-c1d2-bfd1bce3f7f3_a23eb48b-9447-8aaa-3d70-8549fec90ad9",
#                       "analysis_output_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/wgtsQc/20240719dd1ffb82/"
#                     },
#                     "user_reference": "umccr--automated--wgtsqc--4-2-4--20240719dd1ffb82",
#                     "project_id": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#                     "pipeline_id": "71f094dc-0cf8-4fcf-890c-9f3edf00ee20",
#                     "ica_logs_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/logs/wgtsQc/20240719dd1ffb82/",
#                     "analysis_output_uri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/analysis/wgtsQc/20240719dd1ffb82/",
#                     "input_json": "{\"reference_tar\":{\"class\":\"File\",\"location\":\"icav2://92bc8608-9393-44b4-bf16-fb0c5a12269a/dragen-hash-tables/v9-r3/hg38-alt_masked-cnv-hla-rna/\"},\"enable_rna\":true,\"output_directory\":\"L2400251\",\"enable_rrna_filter\":true,\"annotation_file\":{\"class\":\"File\",\"location\":\"icav2://92bc8608-9393-44b4-bf16-fb0c5a12269a/gencode/hg38/v39/gencode.v39.annotation.gtf\"},\"enable_duplicate_marking\":false,\"output_file_prefix\":\"L2400251\",\"fastq_list_rows\":[{\"rgid\":\"GCCCAGTG.CCGCAATT.4\",\"rgsm\":\"L2400251\",\"rglb\":\"L2400251\",\"lane\":4,\"read_1\":{\"class\":\"File\",\"location\":\"icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R1_001.fastq.gz\"},\"read_2\":{\"class\":\"File\",\"location\":\"icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_4/L2400251/L2400251_S23_L004_R2_001.fastq.gz\"}}],\"enable_rna_quantification\":true,\"enable_map_align_output\":true,\"enable_sort\":true}"
#                   },
#                 context=None
#             ),
#             indent=2
#         )
#     )

# # CRAM CWL Test

# if __name__ == "__main__":
#     import os
#
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "workflow_type": "cwl",
#                     "user_tags": {},
#                     "technical_tags": {
#                         "portal_run_id": "20240728cae96835",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:tnSfn-wfm-ready-event-handler:2eb4406d-4073-9245-a2f8-c4556a70c0c3_0aeda72a-244e-d6df-2292-3aadb06a4a81",
#                         "analysis_output_uri": "icav2://cohort-hmf-pdac-dev/cram_test_run/out/20240728cae96835/"
#                     },
#                     "user_reference": "umccr--automated--tumor-normal--4-2-4--20240728cae96835",
#                     "project_id": "41474e59-91ba-4eec-ad1a-b198562220e4",
#                     "pipeline_id": "3d97bc9f-8716-4fa0-81ce-62ed332e0cdd",
#                     "ica_logs_uri": "icav2://cohort-hmf-pdac-dev/cram_test_run/logs/20240728cae96835/",
#                     "analysis_output_uri": "icav2://cohort-hmf-pdac-dev/cram_test_run/out/20240728cae96835/",
#                     "input_json": "{\"reference_tar\":{\"class\":\"File\",\"location\":\"icav2://92bc8608-9393-44b4-bf16-fb0c5a12269a/dragen-hash-tables/v9-r3/hg38-alt_masked-cnv-hla-rna/hg38-alt_masked.cnv.hla.rna-9-r3.0-1.tar.gz\"},\"enable_sv_somatic\":true,\"output_directory_somatic\":\"CORE01050021T_dragen_somatic\",\"enable_map_align_output_germline\":false,\"cram_reference\":{\"class\":\"File\",\"secondaryFiles\":[{\"class\":\"File\",\"location\":\"icav2://reference-data/genomes/GRCh37/Homo_sapiens.GRCh37.GATK.illumina.fasta.fai\"}],\"location\":\"icav2://reference-data/genomes/GRCh37/Homo_sapiens.GRCh37.GATK.illumina.fasta\"},\"cnv_use_somatic_vc_baf\":true,\"output_file_prefix_germline\":\"CORE01050021R\",\"output_directory_germline\":\"CORE01050021R_dragen_germline\",\"enable_cnv_somatic\":true,\"cram_input\":{\"class\":\"File\",\"secondaryFiles\":[{\"class\":\"File\",\"location\":\"icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021T/CORE01050021R.cram.crai\"}],\"location\":\"icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021T/CORE01050021R.cram\"},\"enable_duplicate_marking\":true,\"enable_hrd_somatic\":true,\"output_file_prefix_somatic\":\"CORE01050021T\",\"tumor_cram_input\":{\"class\":\"File\",\"secondaryFiles\":[{\"class\":\"File\",\"location\":\"icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021T/CORE01050021T.cram.crai\"}],\"location\":\"icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021T/CORE01050021T.cram\"},\"enable_map_align_output_somatic\":true}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )


# S3 CWL Test
# if __name__ == "__main__":
#     import os
#
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "workflow_type": "cwl",
#                     "user_tags": {
#                         "libraryId": "L2400256",
#                         "sampleType": "WTS",
#                         "fastqListRowId": "AACACCTG.CGCATGGG.4.240229_A00130_0288_BH5HM2DSXC.L2400256",
#                         "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC"
#                     },
#                     "technical_tags": {
#                         "portal_run_id": "2024080660be6d5f",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:wgtsQcSfn-wfm-ready-event-handler:67d082ab-4c6c-4403-b719-7e755da2f723",
#                         "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/2024080660be6d5f/"
#                     },
#                     "user_reference": "umccr--automated--wgtsqc--4-2-4--2024080660be6d5f",
#                     "project_id": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#                     "pipeline_id": "413b3c60-a3f5-42eb-a9df-8a77768a8328",
#                     "ica_logs_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/logs/wgtsQc/2024080660be6d5f/",
#                     "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgtsQc/2024080660be6d5f/",
#                     "input_json": "{\"reference_tar\":{\"class\":\"File\",\"location\":\"icav2://reference-data/dragen-hash-tables/v9-r3/hg38-alt_masked-cnv-hla-rna/hg38-alt_masked.cnv.hla.rna-9-r3.0-1.tar.gz\"},\"enable_rna\":true,\"output_directory\":\"L2400256_dragen_alignment\",\"enable_rrna_filter\":true,\"annotation_file\":{\"class\":\"File\",\"location\":\"icav2://reference-data/gencode/hg38/v39/gencode.v39.annotation.gtf\"},\"enable_duplicate_marking\":false,\"output_file_prefix\":\"L2400256\",\"fastq_list_rows\":[{\"rgid\":\"AACACCTG.CGCATGGG.4\",\"rgsm\":\"L2400256\",\"rglb\":\"L2400256\",\"lane\":4,\"read_1\":{\"class\":\"File\",\"location\":\"s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202408055ee629cc/Samples/Lane_4/L2400256/L2400256_S28_L004_R1_001.fastq.gz\"},\"read_2\":{\"class\":\"File\",\"location\":\"s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/240229_A00130_0288_BH5HM2DSXC/202408055ee629cc/Samples/Lane_4/L2400256/L2400256_S28_L004_R2_001.fastq.gz\"}}],\"enable_rna_quantification\":true,\"enable_map_align_output\":true,\"enable_sort\":true}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )

# S3 Nextflow test
# if __name__ == "__main__":
#     import os
#
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "workflow_type": "nextflow",
#                     "user_tags": {
#                         "libraryId": "L2400165",
#                         "fastqListRowIds": [
#                             "ACGCCTTGTT.ACGTTCCTTA.4.240229_A00130_0288_BH5HM2DSXC.L2400165"
#                         ]
#                     },
#                     "technical_tags": {
#                         "portal_run_id": "20240806fa366a28",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:cttsov2Sfn-wfm-ready-event-handler:d684198e-6366-74fb-5297-caf7f137a834_c533665e-c472-57a2-bb37-ee6b68a1d2c1",
#                         "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240806fa366a28/"
#                     },
#                     "user_reference": "umccr--automated--cttsov2--2-6-0--20240806fa366a28",
#                     "project_id": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#                     "pipeline_id": "c2dfdbaa-2074-44c7-8078-d33e13607061",
#                     "ica_logs_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/logs/cttsov2/20240806fa366a28/",
#                     "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240806fa366a28/",
#                     "input_json": "{\"StartsFromFastq\":true,\"sample_sheet\":\"icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/cache/cttsov2/20240806fa366a28/SampleSheet.csv\",\"run_folder\":\"s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/cache/cttsov2/20240806fa366a28/\",\"sample_pair_ids\":\"L2400165\"}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )


# # Analysis storage size test
# if __name__ == "__main__":
#     import os
#
#     os.environ['ICAV2_ACCESS_TOKEN_SECRET_ID'] = "ICAv2JWTKey-umccr-prod-service-dev"
#     os.environ['AWS_PROFILE'] = "umccr-development"
#     os.environ['AWS_REGION'] = "ap-southeast-2"
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "analysis_storage_size": "LARGE",
#                     "workflow_type": "cwl",
#                     "user_tags": {
#                         "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC"
#                     },
#                     "technical_tags": {
#                         "portal_run_id": "202411016290aa4d",
#                         "step_functions_execution_arn": "arn:aws:states:ap-southeast-2:843407916570:execution:oraCompressionSfn-wfm-ready-event-handler:bbdf82d7-b099-46fe-9063-5def7b2272f7",
#                         "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411016290aa4d/"
#                     },
#                     "user_reference": "umccr--automated--ora-compression--2024-10-30--202411016290aa4d",
#                     "project_id": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#                     "pipeline_id": "ba8f618a-842f-4a2f-9b2f-a074c0472218",
#                     "idempotency_key": "202411016290aa4d",
#                     "ica_logs_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/logs/ora-compression/202411016290aa4d/",
#                     "analysis_output_uri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411016290aa4d/",
#                     "input_json": "{\"instrument_run_directory\":{\"class\":\"Directory\",\"basename\":\"241024_A00130_0336_BHW7MVDSXC\",\"location\":\"s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/\"},\"ora_reference\":{\"class\":\"File\",\"location\":\"icav2://reference-data/dragen-ora/v2/ora_reference_v2.tar.gz\"},\"ora_print_file_info\":true}"
#                 },
#                 context=None
#             ),
#             indent=2
#         )
#     )
#
# # {
# #   "analysis_id": "c49ff760-5b3f-480f-a1e0-e29fc3b30781",
# #   "analysis_status": "REQUESTED",
# #   "analysis_return_payload": {
# #     "id": "c49ff760-5b3f-480f-a1e0-e29fc3b30781",
# #     "timeCreated": "2024-11-03T08:22:07Z",
# #     "timeModified": "2024-11-03T08:22:09Z",
# #     "owner": {
# #       "id": "73636fd8-692b-375c-9081-d416cd6a4357"
# #     },
# #     "tenant": {
# #       "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
# #       "name": "umccr-prod"
# #     },
# #     "reference": "umccr--automated--ora-compression--2024-10-30--202411016290aa4d-c49ff760-5b3f-480f-a1e0-e29fc3b30781",
# #     "userReference": "umccr--automated--ora-compression--2024-10-30--202411016290aa4d",
# #     "pipeline": {
# #       "id": "ba8f618a-842f-4a2f-9b2f-a074c0472218",
# #       "timeCreated": "2024-10-30T04:22:10Z",
# #       "timeModified": "2024-10-30T04:22:13Z",
# #       "owner": {
# #         "id": "fdb409d3-f99f-34d7-92d8-a6921e44c4be"
# #       },
# #       "tenant": {
# #         "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
# #         "name": "umccr-prod"
# #       },
# #       "code": "dragen-instrument-run-fastq-to-ora-pipeline__4_2_4__20241030041958",
# #       "description": "GitHub Release URL: https://github.com/umccr/cwl-ica/releases/tag/dragen-instrument-run-fastq-to-ora-pipeline/4.2.4__20241030041958",
# #       "language": "CWL",
# #       "pipelineTags": {
# #         "technicalTags": []
# #       },
# #       "analysisStorage": {
# #         "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
# #         "name": "Small",
# #         "description": "1.2TB"
# #       },
# #       "urn": "urn:ilmn:ica:pipeline:ba8f618a-842f-4a2f-9b2f-a074c0472218#dragen-instrument-run-fastq-to-ora-pipeline__4_2_4__20241030041958",
# #       "status": "RELEASED",
# #       "proprietary": false,
# #       "null": "XML"
# #     },
# #     "status": "REQUESTED",
# #     "tags": {
# #       "technicalTags": [
# #         "portal_run_id=202411016290aa4d",
# #         "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:oraCompressionSfn-wfm-ready-event-handler:bbdf82d7-b099-46fe-9063-5def7b2272f7",
# #         "analysis_output_uri=s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411016290aa4d/"
# #       ],
# #       "userTags": [
# #         "instrument_run_id=241024_A00130_0336_BHW7MVDSXC"  # pragma: allowlist secret
# #       ],
# #       "referenceTags": []
# #     },
# #     "analysisStorage": {
# #       "id": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
# #       "name": "Large",
# #       "description": "7.2TB"
# #     },
# #     "analysisPriority": "MEDIUM"
# #   },
# #   "analysis_launch_payload": {
# #     "userReference": "umccr--automated--ora-compression--2024-10-30--202411016290aa4d",
# #     "pipelineId": "ba8f618a-842f-4a2f-9b2f-a074c0472218",
# #     "analysisInput": {
# #       "objectType": "JSON",
# #       "inputJson": "{\n  \"instrument_run_directory\": {\n    \"class\": \"Directory\",\n    \"basename\": \"241024_A00130_0336_BHW7MVDSXC\",\n    \"location\": \"ea19a3f5-ec7c-4940-a474-c31cd91dbad4/fol.e77c7a60e27d4eea125508dcf7906b20/20241030c613872c\"\n  },\n  \"ora_reference\": {\n    \"class\": \"File\",\n    \"location\": \"92bc8608-9393-44b4-bf16-fb0c5a12269a/fil.3f573b26c22c4507077908dcb063a68d/ora_reference_v2.tar.gz\"\n  },\n  \"ora_print_file_info\": true\n}",
# #       "mounts": [
# #         {
# #           "dataId": "fol.e77c7a60e27d4eea125508dcf7906b20",
# #           "mountPath": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4/fol.e77c7a60e27d4eea125508dcf7906b20/20241030c613872c"
# #         },
# #         {
# #           "dataId": "fil.3f573b26c22c4507077908dcb063a68d",
# #           "mountPath": "92bc8608-9393-44b4-bf16-fb0c5a12269a/fil.3f573b26c22c4507077908dcb063a68d/ora_reference_v2.tar.gz"
# #         }
# #       ],
# #       "externalData": [],
# #       "dataIds": [
# #         "fol.e77c7a60e27d4eea125508dcf7906b20",
# #         "fil.3f573b26c22c4507077908dcb063a68d"
# #       ]
# #     },
# #     "tags": {
# #       "technicalTags": [
# #         "portal_run_id=202411016290aa4d",
# #         "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:oraCompressionSfn-wfm-ready-event-handler:bbdf82d7-b099-46fe-9063-5def7b2272f7",
# #         "analysis_output_uri=s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/ora-compression/202411016290aa4d/"
# #       ],
# #       "userTags": [
# #         "instrument_run_id=241024_A00130_0336_BHW7MVDSXC"  # pragma: allowlist secret
# #       ],
# #       "referenceTags": []
# #     },
# #     "activationCodeDetailId": "103094d2-e932-4e34-8dd4-06ee1fb8be68",
# #     "analysisStorageId": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
# #     "analysisOutput": [
# #       {
# #         "sourcePath": "out/",
# #         "targetProjectId": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
# #         "targetPath": "/ora-compression/202411016290aa4d/",
# #         "type": "FOLDER"
# #       }
# #     ]
# #   }
# # }