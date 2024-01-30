#!/usr/bin/env python3

"""
Handle the workflow session object

The workflow session object looks something like this:

{
  "correlationId": "cc85de53-d3d6-4b9b-8b2d-b4a082513adb",
  "timestamp": "2024-01-17T01:43:21.404Z",
  "eventCode": "ICA_EXEC_028",
  "eventParameters": {
    "pipelineExecution": "a154ab78-925a-40d8-8f3e-9c065c4e4acb",
    "analysisPreviousStatus": "INPROGRESS",
    "analysisStatus": "SUCCEEDED"
  },
  "description": "Analysis status changed",
  "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
  "payload": {
    "id": "a154ab78-925a-40d8-8f3e-9c065c4e4acb",
    "timeCreated": "2024-01-17T00:23:17Z",
    "timeModified": "2024-01-17T01:43:18Z",
    "ownerId": "0c51d29a-8ffa-38e9-bf18-736330d7c65a",
    "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
    "tenantName": "umccr-prod",
    "reference": "NovaSeqX-Demo_3664cd_3a7062-BclConvert v4_2_7-0ff58e03-efc1-4e25-bdf5-e3ea835df5dc",
    "userReference": "NovaSeqX-Demo_3664cd_3a7062",
    "pipeline": {
      "id": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca",
      "timeCreated": "2023-11-13T22:16:50Z",
      "timeModified": "2023-11-16T22:08:46Z",
      "ownerId": "88de7b1d-bd37-37e8-8d29-6213bd79e976",
      "tenantId": "55cb0a54-efab-4584-85da-dc6a0197d4c4",
      "tenantName": "ilmn-dragen",
      "code": "BclConvert v4_2_7",
      "urn": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7",
      "description": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
      "language": "NEXTFLOW",
      "languageVersion": {
        "id": "b1585d18-f88c-4ca0-8d47-34f6c01eb6f3",
        "name": "22.04.3",
        "language": "NEXTFLOW"
      },
      "pipelineTags": {
        "technicalTags": []
      },
      "analysisStorage": {
        "id": "8bc4695d-5b20-43a8-aea3-181b4bf6f07e",
        "timeCreated": "2023-02-16T21:36:11Z",
        "timeModified": "2023-05-31T16:38:09Z",
        "ownerId": "dda792d4-7e9c-3c5c-8d0b-93f0cdddd701",
        "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
        "tenantName": "ica-cp-admin",
        "name": "XLarge",
        "description": "16TB"
      }
    },
    "workflowSession": {
      "id": "2549717d-ee16-47c2-b12e-59908b980fd7",
      "timeCreated": "2024-01-17T00:16:17Z",
      "ownerId": "0c51d29a-8ffa-38e9-bf18-736330d7c65a",
      "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
      "tenantName": "umccr-prod",
      "userReference": "ws_NovaSeqX-Demo_3664cd",
      "workflow": {
        "id": "975875cc-41d3-4992-93af-48cc4a26039b",
        "code": "ica_workflow_1_2-21",
        "urn": "urn:ilmn:ica:workflow:975875cc-41d3-4992-93af-48cc4a26039b#ica_workflow_1_2-21",
        "description": "ICA Workflow v2.21.0",
        "languageVersion": {
          "id": "2483549a-1530-4973-bb00-f3f6ccb7e610",
          "name": "20.10.0",
          "language": "NEXTFLOW"
        },
        "workflowTags": {
          "technicalTags": []
        },
        "analysisStorage": {
          "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
          "timeCreated": "2021-11-05T10:28:20Z",
          "timeModified": "2023-05-31T16:38:26Z",
          "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
          "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
          "tenantName": "ica-cp-admin",
          "name": "Small",
          "description": "1.2TB"
        }
      },
      "status": "INPROGRESS",
      "startDate": "2024-01-17T00:16:29Z",
      "summary": "",
      "tags": {
        "technicalTags": [
          "/ilmn-runs/bssh_aps2-sh-prod_3593591/",
          "20231010_pi1-07_0329_A222N7LTD3",
          "NovaSeqX-Demo",
          "3664cd46-7ecb-44c5-b17d-dd442437d61b"
        ],
        "userTags": [
          "/ilmn-runs/bssh_aps2-sh-prod_3593591/"
        ]
      }
    },
    "status": "SUCCEEDED",
    "startDate": "2024-01-17T00:23:25Z",
    "endDate": "2024-01-17T01:39:09Z",
    "summary": "",
    "analysisStorage": {
      "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
      "timeCreated": "2021-11-05T10:28:20Z",
      "timeModified": "2023-05-31T16:38:26Z",
      "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
      "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
      "tenantName": "ica-cp-admin",
      "name": "Small",
      "description": "1.2TB"
    },
    "analysisPriority": "MEDIUM",
    "tags": {
      "technicalTags": [
        "RUN_ID",
        "RUN_NAME",
        "UNIQUE_ID"
      ],
      "userTags": [],
      "referenceTags": []
    }
  }

This returns a manifest where each key is a source uri and the values are a list of destination uris
for where that file will go.

The output will look something like this

{
  "icav2://project_id/path/to/src/file1": [
    "icav2://project_id/path/to/dest/folder1/",
    "icav2://project_id/path/to/dest/folder2/",
  ],
  "icav2://project_id/path/to/src/file2": [
    "icav2://project_id/path/to/dest/folder2/",
    "icav2://project_id/path/to/dest/folder3/",
  ],
}


"""

# Imports
import json
from pathlib import Path
from typing import Dict
import pandas as pd

# Local imports
from bssh_manager_tools.utils.manifest_handlers import generate_run_manifest
from bssh_manager_tools.utils.metadata_handler import get_library_id_assay
from bssh_manager_tools.utils.sample_handlers import get_fastq_list_paths_from_bssh_output_and_fastq_list_csv
from bssh_manager_tools.utils.workflow_session_handler import (
    get_bclconvert_analysis_id_from_workflow_session_detail, get_basespace_run_id_from_bssh_json_output,
    generate_bclconvert_output_folder_path, get_output_project_id_from_ssm_parameter, get_cttso_fastq_cache_path,
    get_cttso_run_cache_path
)
from bssh_manager_tools.utils.icav2_project_data_handler import (
    get_icav2_file_contents, get_data_object_from_id,
    get_uri_from_project_id_and_path
)
from bssh_manager_tools.utils.icav2_configuration_handler import set_icav2_env_vars
from bssh_manager_tools.utils.icav2_analysis_helpers import (
    get_bssh_json_file_id_from_analysis_output_list,
    get_outputs_object_from_analysis_id, get_run_info_xml_file_id_analysis_output_list,
    get_fastq_list_csv_file_id_from_analysis_output_list, get_samplesheet_path_from_analysis_output_list
)
from bssh_manager_tools.utils.xml_helpers import parse_runinfo_xml, get_run_id_from_run_info_xml_dict


def handler(event, context):
    """
    Read in the event and collect the workflow session details
    """
    # Set ICAv2 configuration from secrets
    set_icav2_env_vars()

    # Get the BCLConvert analysis ID
    project_id = event['projectId']
    analysis_id = get_bclconvert_analysis_id_from_workflow_session_detail(event)

    # Get the analysis output path
    output_folder_id, output_data_list = get_outputs_object_from_analysis_id(
        project_id=project_id,
        analysis_id=analysis_id
    )

    # Get the output folder object
    output_folder_obj = get_data_object_from_id(
        project_id=project_id,
        data_id=output_folder_id
    )

    # Get the bssh_json
    bssh_output_file_id = get_bssh_json_file_id_from_analysis_output_list(output_data_list)

    # Read the json object
    bssh_json_dict = json.loads(
        get_icav2_file_contents(
            project_id=project_id,
            file_id=bssh_output_file_id
        )
    )

    # Get the basespace run id from the bssh output dict
    basespace_run_id = get_basespace_run_id_from_bssh_json_output(bssh_json_dict)

    # Get run info (to collect the run id)
    run_info_file_id = get_run_info_xml_file_id_analysis_output_list(
        output_data_list
    )

    # Read in the run info xml
    run_info_dict = parse_runinfo_xml(
        get_icav2_file_contents(
            project_id=project_id,
            file_id=run_info_file_id
        )
    )

    # Collect the run id from the run info xml
    run_id = get_run_id_from_run_info_xml_dict(run_info_dict)

    # Get the samplesheet id
    # The samplesheet needs to be placed in every cttso directory
    samplesheet_path = get_samplesheet_path_from_analysis_output_list(
        output_data_list
    )

    # Get the samplesheet as URI
    samplesheet_as_uri = get_uri_from_project_id_and_path(
        project_id=project_id,
        data_path=samplesheet_path
    )

    # Get fastq list csv
    fastq_list_csv_file_id = get_fastq_list_csv_file_id_from_analysis_output_list(output_data_list)
    fastq_list_csv_pd = pd.DataFrame(
        json.loads(
            get_icav2_file_contents(
                project_id=project_id,
                file_id=fastq_list_csv_file_id
            )
        )
    )

    # Merge the fastq list csv and the bssh output generation to collect the fastq paths
    # Return value is a dictionary where each key is a sample ID, and the list are the absolute fastq paths
    fastq_list_paths: Dict = get_fastq_list_paths_from_bssh_output_and_fastq_list_csv(
        fastq_list_pd=fastq_list_csv_pd,
        bssh_output_dict=bssh_json_dict
    )

    # Generate the manifest output for all files in the output directory
    # to link to the standard output path from the run id
    run_manifest: Dict = generate_run_manifest(
        root_run_uri=get_uri_from_project_id_and_path(project_id, output_folder_obj.data.details.path),
        project_data_list=output_data_list,
        output_project_id=get_output_project_id_from_ssm_parameter(),
        # <bclconvert_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id>
        output_folder_path=generate_bclconvert_output_folder_path(
            run_id=run_id,
            basespace_run_id=basespace_run_id,
        )
    )

    # Query the samples from the bssh sample outputs to determine if there are any samples that need to be added
    # to the cttso run cache path
    for library_id in fastq_list_csv_pd["RGSM"].unique().tolist():
        # For each of the ctTSO files, add a destination matching
        # <cttso_run_cache_path> / <library_id> / <run_name> / <library_id> / <fastq_path>
        # If a user wants to run with topups, these will need to be manually copied over to the destination
        if get_library_id_assay(library_id) == "ctTSO":
            # Copy the samplesheet over to the cttso run cache path
            # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> / <run_id>
            run_manifest[samplesheet_as_uri].append(
                get_cttso_run_cache_path(
                    run_id=run_id,
                    basespace_run_id=basespace_run_id,
                    library_id=library_id,
                )
            )

            # <cttso_run_cache_path> / <YYYY> / <MM> / <run_id> / <basespace_run_id> / <library_id> / <run_id> / <library_id>
            for fastq_path in fastq_list_paths.get(library_id):
                fastq_uri = get_uri_from_project_id_and_path(
                    project_id=project_id,
                    data_path=Path(output_folder_obj.data.details.path) / fastq_path
                )
                run_manifest[fastq_uri].append(
                    get_cttso_fastq_cache_path(
                        run_id=run_id,
                        basespace_run_id=basespace_run_id,
                        library_id=library_id,
                    )
                )

    # Return the manifest file
    return run_manifest
