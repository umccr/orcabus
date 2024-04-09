#!/usr/bin/env python

"""
The icav2 event translator expects the following as inputs

{
  "correlationId": "94739e11-f3dc-486b-8a85-2d5a9e237b52",
  "timestamp": "2024-03-25T10:07:09.990Z",
  "eventCode": "ICA_EXEC_028",
  "eventParameters": {
    "pipelineExecution": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
    "analysisPreviousStatus": "INPROGRESS",
    "analysisStatus": "SUCCEEDED"
  },
  "description": "Analysis status changed",
  "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
  "payloadVersion": "v3",
  "payload": {
    "id": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
    "timeCreated": "2024-03-25T08:04:40Z",
    "timeModified": "2024-03-25T10:07:06Z",
    "ownerId": "a9938581-7bf5-35d2-b461-282f34794dd1",
    "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
    "tenantName": "umccr-prod",
    "reference": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192-BclConvert v4_2_7-247cebc9-bacb-40fd-a13c-513cf713e36b",
    "userReference": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192",
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
      },
      "proprietary": false
    },
    "workflowSession": {
      "id": "89323106-f36c-433a-ba3b-00682a89f84b",
      "timeCreated": "2024-03-25T07:57:35Z",
      "ownerId": "a9938581-7bf5-35d2-b461-282f34794dd1",
      "tenantId": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
      "tenantName": "umccr-prod",
      "userReference": "ws_240229_A00130_0288_BH5HM2DSXC_844951",
      "workflow": {
        "id": "d691d76a-3a98-4669-ae09-088fb4c4b47d",
        "code": "ica_workflow_1_2-23",
        "urn": "urn:ilmn:ica:workflow:d691d76a-3a98-4669-ae09-088fb4c4b47d#ica_workflow_1_2-23",
        "description": "ICA Workflow v2.23.0",
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
      "startDate": "2024-03-25T07:57:48Z",
      "summary": "",
      "tags": {
        "technicalTags": [
          "/ilmn-runs/bssh_aps2-sh-prod_3882885/",
          "240229_A00130_0288_BH5HM2DSXC",
          "844951f7-6d66-449d-9212-495009437e3c"
        ],
        "userTags": [
          "/ilmn-runs/bssh_aps2-sh-prod_3882885/"
        ]
      }
    },
    "status": "SUCCEEDED",
    "startDate": "2024-03-25T08:04:51Z",
    "endDate": "2024-03-25T10:07:05Z",
    "summary": "",
    "analysisStorage": {
      "id": "3fab13dd-46e7-4b54-bb34-b80a01a99379",
      "timeCreated": "2021-11-05T10:28:20Z",
      "timeModified": "2023-05-31T16:38:14Z",
      "ownerId": "8ec463f6-1acb-341b-b321-043c39d8716a",
      "tenantId": "f91bb1a0-c55f-4bce-8014-b2e60c0ec7d3",
      "tenantName": "ica-cp-admin",
      "name": "Large",
      "description": "7.2TB"
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
}


The event tranlator then returns the following

{
  "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
  "analysisId": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
  "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
  
  "tags": {
    "technicalTags": [
      "/ilmn-runs/bssh_aps2-sh-prod_3882885/",
      "240229_A00130_0288_BH5HM2DSXC",
      "844951f7-6d66-449d-9212-495009437e3c"
    ],
    "userTags": [
      "/ilmn-runs/bssh_aps2-sh-prod_3882885/"
    ]
  }
}

"""
import re

def icav2_event_translator_handler(event, context):

    # Extract relevant fields from the event payload
    projectId = event.get("projectId")
    eventCode = event.get("eventCode")
    eventParameters = event.get("eventParameters", {})
    analysisStatus = eventParameters.get("analysisStatus")
    payload = event.get("payload", {})
    analysisId = payload.get("id")
    pipeline_id = payload.get("pipeline", {}).get("id")
    userReference = payload.get("userReference")
    
    # define event tags for internal event (from workflow session)
    tags = payload.get("workflowSession", {}).get("tags", {})

    # Check conditions for the event to be processed: 
    # eventCode is ICA_EXEC_028, analysisStatus is SUCCEEDED,
    # payload.pipeline.id is "bf93b5cf-cb27-4dfa-846e-acd6eb081aca", 
    # and userReference matches the regex pattern
    if (
        eventCode == "ICA_EXEC_028" 
        and analysisStatus == "SUCCEEDED" 
        and pipeline_id == "bf93b5cf-cb27-4dfa-846e-acd6eb081aca" 
        and re.match(r"\d{6}_[A|B]\d+_\d{4}_\w+", userReference)
    ):
        # Generate internal event with required attributes
        internal_event = {
            "projectId": projectId,
            "analysisId": analysisId,
            "instrumentRunId": '_'.join(userReference.split('_')[:4]),
            "tags": tags
        }
        
        # For now, just return the internal event
        return internal_event
    else:
        # Conditions not met, throw an error
        raise ValueError("Event does not meet processing conditions.")
