#!/usr/bin/env bash

set -euo pipefail

data_json="$( \
  jq --null-input --raw-output \
    '
      {
        "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22",
        "analysisId": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
        "userReference": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192",
        "timeCreated": "2024-03-25T08:04:40Z",
        "timeModified": "2024-03-25T10:07:06Z",
        "pipelineId": "bf93b5cf-cb27-4dfa-846e-acd6eb081aca",
        "pipelineCode": "BclConvert v4_2_7",
        "pipelineDescription": "This is an autolaunch BclConvert pipeline for use by the metaworkflow",
        "pipelineUrn": "urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7",
        "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
        "basespaceRunId": 3882885,
        "samplesheetB64gz": "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"  # pragma: allowlist secret
      }
    ' \
)"                                                                                                                                                                        

payload_json="$( \
  jq --null-input --raw-output \
    --argjson data_json "${data_json}" \
    '
      {
        "refId": null,
        "version": "0.1.0",
        "data": $data_json
      }
    ' \
)"

portal_run_id="$(date +"%Y%m%d")$(xxd -l 4 -c 4 -p < /dev/random)"

detail_json="$( \
  jq --null-input --raw-output \
    --argjson payload_json "${payload_json}" \
    --arg portal_run_id "${portal_run_id}" \
    '
      {
        "portalRunId": $portal_run_id,
        "timestamp": "2024-05-28T06:17:07Z",
        "status": "SUCCEEDED",
        "workflowName": "BclConvert",
        "workflowVersion": "4.2.7",
        "workflowRunName": "240229_A00130_0288_BH5HM2DSXC_844951_4ce192",
        "payload": $payload_json
      }
    '
)"

event_entry="$( \
  jq --null-input --raw-output --compact-output \
    --arg utc_time "$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')" \
    --argjson input_detail "${detail_json}" \
    '
      {
        "Entries": [
          {
            "EventBusName": "OrcaBusMain",
            "DetailType": "WorkflowRunStateChange",
            "Source": "orcabus.bclconvertmanager",
            "Time": $utc_time,
            "Resources": [],
            "Detail": ( $input_detail | tojson )
          }
        ]
      }
    ' \
)"

aws events put-events --cli-input-json "${event_entry}" 
