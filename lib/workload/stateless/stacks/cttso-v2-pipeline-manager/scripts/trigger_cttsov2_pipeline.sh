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
SOURCE="manual"
WORKFLOW_NAME="cttsov2"
WORKFLOW_VERSION="2.6.0"

#############
# GLOCALS
#############

# Inputs
SAMPLE_ID="L2401145"
INSTRUMENT_RUN_ID="HMF22DSXC"
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
          "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
          "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
          "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143",
          "mask_short_reads": 35,
          "adapter_behavior": "trim",
          "minimum_trimmed_read_length": 35
        },
        "bclconvert_data": [
          {
            "lane": 4,
            "sample_id": "L2401145",
            "index": "ACTGCTTA",
            "index2": "AGAGGCGC"
          }
        ],
        "tso500l_settings": {
          "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
          "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
          "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143",
          "mask_short_reads": 35,
          "adapter_behavior": "trim",
          "minimum_trimmed_read_length": 35
        },
        "tso500l_data": [
          {
            "sample_id": "L2401145",
            "sample_type": "DNA",
            "lane": 4,
            "index": "ACTGCTTA",
            "index2": "AGAGGCGC"
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
          "rgid": "ACTGCTTA.AGAGGCGC.4",
          "rgsm": "L2401145",
          "rglb": "L2401145",
          "lane": 4,
          "read1FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ctdna_v1_test_data/inputs/SBJ00596/L2401145_S6_L004_R1_001.fastq.gz",
          "read2FileUri": "icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ctdna_v1_test_data/inputs/SBJ00596/L2401145_S6_L004_R2_001.fastq.gz"
        }
      ]
    '
)"

# RUNTIME
PROJECT_NAME="development"
PROJECT_ID="ea19a3f5-ec7c-4940-a474-c31cd91dbad4"
WORKFLOW_RUN_NAME_PREFIX="umccr__semi_automated__cttsov2__2_6_0__"
PORTAL_RUN_ID="$(date +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"
CACHE_URI_PREFIX="icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ctdna_v1_test_data/cache/SBJ00596/"

# Outputs
ANALYSIS_OUTPUT_URI_PREFIX="icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ctdna_v1_test_data/out/SBJ00596/"
ICA_LOGS_URI_PREFIX="icav2://ea19a3f5-ec7c-4940-a474-c31cd91dbad4/ctdna_v1_test_data/logs/SBJ00596/"


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
        "inputs": {
          "sampleId": $sample_id,
          "samplesheet": $samplesheet,
          "fastqListRows": $fastq_list_rows,
          "instrumentRunId": $instrument_run_id
        },
        "engineParameters": {
          "projectId": $project_id,
          "cacheUri": "\($cache_uri_prefix)\($portal_run_id)/",
          "outputUri": "\($analysis_output_uri_prefix)\($portal_run_id)/",
          "logsUri": "\($ica_logs_uri_prefix)\($portal_run_id)/"
        }
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
