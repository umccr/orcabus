#!/usr/bin/env bash

set -euo pipefail

: '
Trigger the cttso v2 pipeline
'

#############
# GLOBALS
#############

EVENT_BUS_NAME="OrcaBusMain"
DETAIL_TYPE="WorkflowRunStateChange"
SOURCE="orcabus.cttsov2inputeventglue"
WORKFLOW_NAME="cttsov2"
WORKFLOW_VERSION="2.1.1"

#############
# GLOCALS
#############

# Inputs
SAMPLE_ID="L2400160"
INSTRUMENT_RUN_ID="240229_A00130_0288_BH5HM2DSXC"
SAMPLESHEET_JSON="$(
  jq --null-input --raw-output \
    '
      {
        "header": {
          "file_format_version": 2,
          "run_name": "Tsqn240214-26-ctTSOv2_29Feb24",
          "instrument_type": "NovaSeq"
        },
        "reads": {
          "read_1_cycles": 151,
          "read_2_cycles": 151,
          "index_1_cycles": 10,
          "index_2_cycles": 10
        },
        "bclconvert_settings": {
          "adapter_read_1": "CTGTCTCTTATACACATCT",
          "adapter_read_2": "CTGTCTCTTATACACATCT",
          "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
          "mask_short_reads": 35,
          "adapter_behavior": "trim",
          "minimum_trimmed_read_length": 35
        },
        "bclconvert_data": [
          {
            "lane": 1,
            "sample_id": "L2400160",
            "index": "AGAGGCAACC",
            "index2": "CCATCATTAG",
            "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
            "adapter_read_1": "CTGTCTCTTATACACATCT",
            "adapter_read_2": "CTGTCTCTTATACACATCT"
          }
        ],
        "tso500l_settings": {
          "adapter_read_1": "CTGTCTCTTATACACATCT",
          "adapter_read_2": "CTGTCTCTTATACACATCT",
          "override_cycles": "U7N1Y143;I10;I10;U7N1Y143",
          "mask_short_reads": 35,
          "adapter_behavior": "trim",
          "minimum_trimmed_read_length": 35
        },
        "tso500l_data": [
          {
            "sample_id": "L2400160",
            "sample_type": "DNA",
            "lane": 1,
            "index": "AGAGGCAACC",
            "index2": "CCATCATTAG",
            "i7_index_id": "UDP0018",
            "i5_index_id": "UDP0018"
          }
        ]
      }
    '
)"
FASTQ_LIST_ROWS="$( \
  jq --null-input --raw-output \
    '
      [
        {
          "RGID": "AGAGGCAACC.CCATCATTAG.1",
          "RGSM": "L2400160",
          "RGLB": "L2400160",
          "Lane": 1,
          "Read1FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405315b17f6c9/Samples/Lane_1/L2400160/L2400160_S3_L001_R1_001.fastq.gz",
          "Read2FileUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405315b17f6c9/Samples/Lane_1/L2400160/L2400160_S3_L001_R2_001.fastq.gz"
        }
      ]
    '
)"

# RUNTIME
PROJECT_NAME="trial"
PROJECT_ID="7595e8f2-32d3-4c76-a324-c6a85dae87b5"
WORKFLOW_RUN_NAME_PREFIX="umccr__automated__cttsov2__2_1_1__"
PORTAL_RUN_ID="$(date +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"
CACHE_URI_PREFIX="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_cache/cttsov2/2_1_1/"

# Outputs
ANALYSIS_OUTPUT_URI_PREFIX="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/cttsov2/2_1_1/"
ICA_LOGS_URI_PREFIX="icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_logs/cttsov2/2_1_1/"


###############
# GENERATE DATA
###############
data_json="$( \
  jq --null-input --raw-output \
    --arg project_name "${PROJECT_NAME}" \
    --arg project_id "${PROJECT_ID}" \
    --arg portal_run_id "${PORTAL_RUN_ID}" \
    --arg sample_id "${SAMPLE_ID}" \
    --arg instrument_run_id "${INSTRUMENT_RUN_ID}" \
    --argjson samplesheet "${SAMPLESHEET_JSON}" \
    --argjson fastq_list_rows "${FASTQ_LIST_ROWS}" \
    --arg cache_uri_prefix "${CACHE_URI_PREFIX}" \
    --arg analysis_output_uri_prefix "${ANALYSIS_OUTPUT_URI_PREFIX}" \
    --arg ica_logs_uri_prefix "${ICA_LOGS_URI_PREFIX}" \
    '
      {
        "userTags": {
          "project_name": $project_name,
          "instrument_run_id": $instrument_run_id
        },
        "sampleId": $sample_id,
        "samplesheet": $samplesheet,
        "fastqListRows": $fastq_list_rows,
        "cacheUri": "\($cache_uri_prefix)\($portal_run_id)/",
        "analysisOutputUri": "\($analysis_output_uri_prefix)\($portal_run_id)/",
        "icaLogsUri": "\($ica_logs_uri_prefix)\($portal_run_id)/",
        "instrumentRunId": $instrument_run_id,
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
