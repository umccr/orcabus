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
WORKFLOW_NAME="tumor_normal"
WORKFLOW_VERSION="4.2.4"

#############
# GLOCALS
#############

# Inputs
NORMAL_CRAM_URI="icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021R/cram/CORE01050021R.cram"
TUMOR_CRAM_URI="icav2://cohort-hmf-pdac-dev/cram_test_data/CORE01050021T/cram/CORE01050021T.cram"
CRAM_REFERENCE_URI="icav2://reference-data/genomes/GRCh37/Homo_sapiens.GRCh37.GATK.illumina.fasta"
PIPELINE_ID="3d97bc9f-8716-4fa0-81ce-62ed332e0cdd"  # Custom pipeline id with the cram options

# RUNTIME
PROJECT_NAME="cohort-hmf-pdac-dev"
PROJECT_ID="41474e59-91ba-4eec-ad1a-b198562220e4"
WORKFLOW_RUN_NAME_PREFIX="umccr--automated--tumor-normal--4-2-4--"
PORTAL_RUN_ID="$(date +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"

# Outputs
ANALYSIS_OUTPUT_URI_PREFIX="icav2://cohort-hmf-pdac-dev/cram_test_run/out/"
CACHE_URI_PREFIX="icav2://cohort-hmf-pdac-dev/cram_test_run/cache/"
ICA_LOGS_URI_PREFIX="icav2://cohort-hmf-pdac-dev/cram_test_run/logs/"

###############
# GENERATE DATA
###############
data_json="$( \
  jq --null-input --raw-output \
    --arg cram_uri "${NORMAL_CRAM_URI}" \
    --arg tumor_cram_uri "${TUMOR_CRAM_URI}" \
    --arg cram_reference_uri "${CRAM_REFERENCE_URI}" \
    --arg project_name "${PROJECT_NAME}" \
    --arg portal_run_id "${PORTAL_RUN_ID}" \
    --arg project_id "${PROJECT_ID}" \
    --arg pipeline_id "${PIPELINE_ID}" \
    --arg cache_uri_prefix "${CACHE_URI_PREFIX}" \
    --arg analysis_output_uri_prefix "${ANALYSIS_OUTPUT_URI_PREFIX}" \
    --arg ica_logs_uri_prefix "${ICA_LOGS_URI_PREFIX}" \
    '
      {
        "inputs": {
          "enableDuplicateMarking": true,
          "enableCnvSomatic": true,
          "enableHrdSomatic": true,
          "enableSvSomatic": true,
          "cnvUseSomaticVcBaf": true,
          "outputPrefixSomatic": "CORE01050021T",
          "outputPrefixGermline": "CORE01050021R",
          "dragenReferenceVersion": "v9-r3",
          "cramInput": $cram_uri,
          "tumorCramInput": $tumor_cram_uri,
          "cramReference": $cram_reference_uri
        },
        "engineParameters": {
          "projectId": $project_id,
          "pipelineId": $pipeline_id,
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
