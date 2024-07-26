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
FASTQ_LIST_ROWS="$( \
  jq --null-input --raw-output \
    '
      [
        {
          "rgid": "GGAGCGTC.GCACGGAC.2",
          "rgsm": "L2400238",
          "rglb": "L2400238",
          "lane": 2,
          "read1FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R1_001.fastq.gz",
          "read2FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400238/L2400238_S13_L002_R2_001.fastq.gz"
        },
        {
          "rgid": "GGAGCGTC.GCACGGAC.3",
          "rgsm": "L2400238",
          "rglb": "L2400238",
          "lane": 3,
          "read1FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R1_001.fastq.gz",
          "read2FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400238/L2400238_S13_L003_R2_001.fastq.gz"
        }
      ]
    '
)"

TUMOR_FASTQ_LIST_ROWS="$( \
  jq --null-input --raw-output \
    '
      [
        {
          "rgid": "TCGTAGTG.CCAAGTCT.2",
          "rgsm": "L2400231",
          "rglb": "L2400231",
          "lane": 2,
          "read1FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R1_001.fastq.gz",
          "read2FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_2/L2400231/L2400231_S12_L002_R2_001.fastq.gz"
        },
        {
          "rgid": "TCGTAGTG.CCAAGTCT.3",
          "rgsm": "L2400231",
          "rglb": "L2400231",
          "lane": 3,
          "read1FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R1_001.fastq.gz",
          "read2FileUri": "icav2://development/primary/240229_A00130_0288_BH5HM2DSXC/2024071110689063/Samples/Lane_3/L2400231/L2400231_S12_L003_R2_001.fastq.gz"
        }
      ]
    '
)"

# RUNTIME
# Custom pipeline id with the cram options and tmpdirMin set
PIPELINE_ID="3d97bc9f-8716-4fa0-81ce-62ed332e0cdd"
PROJECT_NAME="development"
PROJECT_ID="ea19a3f5-ec7c-4940-a474-c31cd91dbad4"
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
    --argjson fastq_list_rows "${FASTQ_LIST_ROWS}" \
    --argjson tumor_fastq_list_rows "${TUMOR_FASTQ_LIST_ROWS}" \
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
          "outputPrefixSomatic": "L2400231",
          "outputPrefixGermline": "L2400238",
          "dragenReferenceVersion": "v9-r3",
          "fastqListRows": $fastq_list_rows,
          "tumorFastqListRows": $tumor_fastq_list_rows
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

event_entry="$( \
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
