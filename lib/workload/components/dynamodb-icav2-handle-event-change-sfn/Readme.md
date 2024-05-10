# Dynamodb ICAv2 Handle Event Change Step Function

## Summmary

This step function construct listens to ICAv2 events through the main Orcabus event pipe.  

The step function then determines if the ICAv2 analysis ID is in the database, if not, no action is required.  

If the ICav2 analysis ID is in the database, then the step function will update the database with the new event data.

This includes:
  * Updating the status of the analysis in the db_uuid table
  * Appending the status and timestamp in the event logger table

After updating the database, the step function will then release an internal event stating there has been change
to the analysis status.  

## Sfn I/O

Example input event:

<details>

<summary>Click to expand!</summary>

```json
{
  "correlationId": "970362e1-8b48-4943-b52c-32080cc0e150",
  "timestamp": "2024-05-10T09:16:59.299Z",
  "eventCode": "ICA_EXEC_028",
  "eventParameters": {
    "pipelineExecution": "08f8dd73-dd72-4f1a-813b-03d4f32f3614",
    "analysisPreviousStatus": "GENERATING_OUTPUTS",
    "analysisStatus": "SUCCEEDED"
  },
  "description": "Analysis status changed",
  "projectId": "7595e8f2-32d3-4c76-a324-c6a85dae87b5",
  "payloadVersion": "v4",
  "payload": {
    "id": "08f8dd73-dd72-4f1a-813b-03d4f32f3614",
    "timeCreated": "2024-05-10T08:59:47Z",
    "timeModified": "2024-05-10T09:16:55Z",
    "owner": {
      "id": "a9938581-7bf5-35d2-b461-282f34794dd1"
    },
    "tenant": {
      "id": "1555b441-c3be-40b0-a8f0-fb9dc7500545",
      "name": "umccr-prod"
    },
    "reference": "bclconvert_interop__semi_automated__umccr__pipeline-bclconvert-interop-qc__1_3_1--1_21__20240313015132-a9b4cd4e-50d3-4748-a5df-fdbaab254aee",
    "userReference": "bclconvert_interop__semi_automated__umccr__pipeline",
    "pipeline": {
      "id": "f606f580-d476-47a8-9679-9ddb39fcb0a8",
      "urn": "urn:ilmn:ica:pipeline:f606f580-d476-47a8-9679-9ddb39fcb0a8#bclconvert-interop-qc__1_3_1--1_21__20240313015132",
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
      "proprietary": false
    },
    "status": "SUCCEEDED",
    "startDate": "2024-05-10T08:59:53Z",
    "endDate": "2024-05-10T09:16:54Z",
    "summary": "",
    "analysisStorage": {
      "id": "6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0",
      "name": "Small",
      "description": "1.2TB"
    },
    "analysisPriority": "LOW",
    "tags": {
      "technicalTags": [
        "portal_run_id=20240510abcd0021",
        "step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:27d3c64d-cbde-e39f-47b6-78ee7ef63d93_3cd71a8a-d2e9-6a36-f273-5d1129fe125d"
      ],
      "userTags": [
        "projectname=trial"
      ],
      "referenceTags": []
    }
  }
}
```

</details>

The step function will then raise an event like this:

<details>

<summary>Click to expand!</summary>

// FIMXE - has json literals that need to be updated

```json
{
    "version": "0",
    "id": "2c8560b5-ff65-3cfe-b88b-e23948805117",
    "detail-type": "workflowRunStateChange",
    "source": "orcabus.bclconvert_interop_qc",
    "account": "843407916570",
    "time": "2024-05-10T10:06:59Z",
    "region": "ap-southeast-2",
    "resources": [
        "arn:aws:states:ap-southeast-2:843407916570:stateMachine:bclconvertInteropQcSfn-icav2-external-handler",
        "arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-icav2-external-handler:215316fb-8d33-4e86-a070-fe7b8d50f645"
    ],
    "detail": {
        "status": "$.Item.analysis_status.S",
        "workflowType": "bclconvert_interop_qc",
        "workflowVersion": "1.3.1--1.21",
        "payload": {
            "refId": "",
            "analysisReturnPayload": "$.Item.analysis_return_payload.S",
            "stateMachineExecutionArn": "$.Item.state_machine_execution_arn.S",
            "analysisLaunchPayload": "{\"userReference\":\"bclconvert_interop__semi_automated__umccr__pipeline\",\"pipelineId\":\"f606f580-d476-47a8-9679-9ddb39fcb0a8\",\"tags\":{\"technicalTags\":[\"portal_run_id=20240510abcd0021\",\"step_functions_execution_arn=arn:aws:states:ap-southeast-2:843407916570:execution:bclconvertInteropQcSfn-wfm-ready-event-handler:27d3c64d-cbde-e39f-47b6-78ee7ef63d93_3cd71a8a-d2e9-6a36-f273-5d1129fe125d\"],\"userTags\":[\"projectname=trial\"],\"referenceTags\":[]},\"analysisInput\":{\"objectType\":\"JSON\",\"inputJson\":\"{\\n  \\\"bclconvert_report_directory\\\": {\\n    \\\"class\\\": \\\"Directory\\\",\\n    \\\"location\\\": \\\"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.81ad1cb41b92470d530608dc3cf57419/Reports\\\"\\n  },\\n  \\\"interop_directory\\\": {\\n    \\\"class\\\": \\\"Directory\\\",\\n    \\\"location\\\": \\\"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.454782a16e9342b9e4e808dc388cff32/InterOp\\\"\\n  },\\n  \\\"run_id\\\": \\\"231116_A01052_0172_BHVLM5DSX7\\\"\\n}\",\"mounts\":[{\"dataId\":\"fol.81ad1cb41b92470d530608dc3cf57419\",\"mountPath\":\"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.81ad1cb41b92470d530608dc3cf57419/Reports\"},{\"dataId\":\"fol.454782a16e9342b9e4e808dc388cff32\",\"mountPath\":\"7595e8f2-32d3-4c76-a324-c6a85dae87b5/fol.454782a16e9342b9e4e808dc388cff32/InterOp\"}],\"externalData\":[],\"dataIds\":[\"fol.81ad1cb41b92470d530608dc3cf57419\",\"fol.454782a16e9342b9e4e808dc388cff32\"]},\"activationCodeDetailId\":\"103094d2-e932-4e34-8dd4-06ee1fb8be68\",\"analysisStorageId\":\"6e1b6c8f-f913-48b2-9bd0-7fc13eda0fd0\",\"outputParentFolderId\":null,\"analysisOutput\":[{\"sourcePath\":\"out/\",\"targetProjectId\":\"7595e8f2-32d3-4c76-a324-c6a85dae87b5\",\"targetPath\":\"/interop_qc/20240510abcd0021/out/\",\"type\":\"FOLDER\"}]}",
            "analysisId": "08f8dd73-dd72-4f1a-813b-03d4f32f3614"
        },
        "serviceVersion": "${__service_version__}",
        "portalRunId": "20240510abcd0021",
        "timestamp": "2024-05-10T10:06:58.813Z"
    }
}
```

</details>

## Construct Inputs

  
* `tableName`: `string`  Name of the table to get / update / query

* `stateMachineName`: `string`  Name of the state machine we create  

* `detailType`: `string`  Name of the event type we're handing (workflowRunStateChange)
* `eventBusName`: `string`  Detail of the eventbus to push the event to (OrcaBusMain)
* `icaEventPipeName`: `string`  Name of the ica event pipe this step function needs to subscribe to  (Not currently used)
* `internalEventSource`: `string`  Source of the event we push  (orcabus.bclconvert_interop_qc)

* `workflowType`: `string`  Type of the workflow we're handling (bclconvert_interop_qc)
* `workflowVersion`: `string`  The workflow Version we're using (1.3.1--1.21)  This is not currently used
* `serviceVersion`: `string`  The service version we're running (2024.05.07)   This is not currently used
