# Workflow Input
bssh_project_id="b23fb516-d852-4985-adcc-831c12e8cd22"     # BSSH-trial
bssh_analysis_id="01bd501f-dde6-42b5-b281-5de60e43e1d7"    # The BCLConvert Analysis ID triggered by BSSH
output_uri="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/"

# Event metadata
portal_run_id="$(date --utc +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"
utc_time="$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')"

# Generate the input payload
input_payload="$( \
  jq --null-input --raw-output \
    --arg bssh_project_id "${bssh_project_id}" \
    --arg bssh_analysis_id "${bssh_analysis_id}" \
    --arg output_uri "${output_uri}" \
    '
      {
        "refId": null,
        "version": "0.1.0",
        "data": {
          "bsshProjectId": $bssh_project_id,
          "bsshAnalysisId": $bssh_analysis_id,
          "outputUri": $output_uri
        }
      }
    '
)"

# Generate the input detail
input_detail="$(
  jq --null-input --raw-output \
    --arg portal_run_id "${portal_run_id}" \
    --argjson input_payload "${input_payload}" \
    '
      {
        "status": "ready",
        "portalRunId": $portal_run_id,
        "workflowName": "bsshFastqCopy",
        "workflowVersion": "1.0.0",
        "payload": $input_payload
      }
    '
)"

# Generate the event entry
event_entry="$(
  jq --null-input --raw-output --compact-output \
    --arg portal_run_id "$portal_run_id" \
    --arg utc_time "$utc_time" \
    --argjson input_detail "$input_detail" \
    '
      {
        "Entries": [
          {
            "EventBusName": "OrcaBusMain",
            "DetailType": "WorkflowRunStateChange",
            "Source": "orcabus.workflowmanager",
            "Time": $utc_time,
            "Resources": [],
            "Detail": ( $input_detail | tojson )
          }
        ]
      }
    ' \
)"

# Push the event to the event bus
aws events put-events --cli-input-json "${event_entry}"