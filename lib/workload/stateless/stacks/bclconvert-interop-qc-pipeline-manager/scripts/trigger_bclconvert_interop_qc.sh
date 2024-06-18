#!/usr/bin/env bash

set -euo pipefail

: '
Trigger the BCLConvert Report InterOp QC Workflow
'

#############
# GLOBALS
#############

EVENT_BUS_NAME="OrcaBusMain"
DETAIL_TYPE="WorkflowRunStateChange"
SOURCE="orcabus.bclconvertinteropqcinputeventglue"
WORKFLOW_NAME="bclconvert_interop_qc"
WORKFLOW_VERSION="1.3.1--1.21__20240410040204"

#############
# GLOCALS
#############

# Inputs
BCLCONVERT_REPORT_DIRECTORY_URI="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/Reports/"
INTEROP_DIRECTORY_URI="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/InterOp/"
INSTRUMENT_RUN_ID="240229_A00130_0288_BH5HM2DSXC"

# RUNTIME
PROJECT_NAME="trial"
PROJECT_ID="7595e8f2-32d3-4c76-a324-c6a85dae87b5"
WORKFLOW_RUN_NAME_PREFIX="umccr__automated__bclconvert_interop_qc__1_3_1__1_21__20240410040204__"
PORTAL_RUN_ID="$(date +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"

# Outputs
ANALYSIS_OUTPUT_URI_PREFIX="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/bclconvert_interop_qc/1_3_1--1_21__20240410040204/"
ICA_LOGS_URI_PREFIX="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_logs/bclconvert_interop_qc/1_3_1--1_21__20240410040204/"


###############
# GENERATE DATA
###############
data_json="$( \
  jq --null-input --raw-output \
    --arg project_name "${PROJECT_NAME}" \
    --arg project_id "${PROJECT_ID}" \
    --arg portal_run_id "${PORTAL_RUN_ID}" \
    --arg bclconvert_report_directory_uri "${BCLCONVERT_REPORT_DIRECTORY_URI}" \
    --arg interop_directory_uri "${INTEROP_DIRECTORY_URI}" \
    --arg instrument_run_id "${INSTRUMENT_RUN_ID}" \
    --arg analysis_output_uri_prefix "${ANALYSIS_OUTPUT_URI_PREFIX}" \
    --arg ica_logs_uri_prefix "${ICA_LOGS_URI_PREFIX}" \
    '
      {
        "userTags": {
          "project_name": $project_name,
          "instrument_run_id": $instrument_run_id
        },
        "bclconvertReportDirectory": "\($bclconvert_report_directory_uri)",
        "interopDirectory": "\($interop_directory_uri)",
        "analysisOutputUri": "\($analysis_output_uri_prefix)\($portal_run_id)/",
        "icaLogsUri": "\($ica_logs_uri_prefix)\($portal_run_id)/",
        "runId": $instrument_run_id,
        "projectId": $project_id
      }
    ' \
)"

###################
# GENERATE PAYLOAD
###################

payload_json="$( \
  jq --null-input --raw-output \
    --argjson data_json "${data_json}" \
    '
      {
        "refId": null,
        "version": "2024.05.24",
        "data": $data_json
      }
    '
)"

###################
# GENERATE DETAIL
###################

detail_json="$( \
  jq --null-input --raw-output \
    --arg portal_run_id "${PORTAL_RUN_ID}" \
    --arg workflow_name "${WORKFLOW_NAME}" \
    --arg workflow_version "${WORKFLOW_VERSION}" \
    --arg workflow_run_name_prefix "${WORKFLOW_RUN_NAME_PREFIX}" \
    --argjson payload_json "${payload_json}" \
    '
      {
        "status": "ready",
        "portalRunId": $portal_run_id,
        "workflowName": $workflow_name,
        "workflowVersion": $workflow_version,
        "workflowRunName": "\($workflow_run_name_prefix)\($portal_run_id)",
        "timestamp": (now | todate),
        "payload": $payload_json
      }
    '
)"

###################
# GENERATE EVENT
###################

event_entry="$(
  jq --null-input --raw-output --compact-output \
    --arg event_bus_name "${EVENT_BUS_NAME}" \
    --arg detail_type "${DETAIL_TYPE}" \
    --arg source "${SOURCE}" \
    --argjson input_detail "${detail_json}" \
    '
      {
        "Entries": [
          {
            "EventBusName": $event_bus_name,
            "DetailType": $detail_type,
            "Source": $source,
            "Detail": ( $input_detail | tojson )
          }
        ]
      }
    ' \
)"

###################
# LAUNCH EVENT
###################

aws events put-events --cli-input-json "${event_entry}"
