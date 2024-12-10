# Tumor Normal Pipeline Manager

This service wraps the ICAv2 dragen TN pipeline, stores inputs and outputs of the pipeline in a DynamoDb database.  

This service receives a READY Workflow Run State Change event for the Dragen Somatic Tumor Normal pipeline, and then launches the workflow on ICAv2.

The pipeline takes input files in any of the following formats:
  * Fastq.gz 
  * Fastq.ora
  * Bam
  * Cram

The data schema for the workflow run state change event can be found [here](docs/ready_data_schema.json)

Steps to generating a launch script with bash

## Part 1 Setting up our global parameters

To run the tumor normal pipeline through the Orcabus system, 
we need to set up the following parameters:

**Input File Parameters**

* Tumor Library ID
* Normal Library ID
* Tumor Fastq List Rows
* Normal Fastq List Rows

**Boolean Parameters**

* enableDuplicateMarking
* enableCnvSomatic
* enableHrdSomatic
* enableSvSomatic
* cnvUseSomaticVcBaf

**Engine Parameters**

* outputUri
* logsUri

**Tags**

* individualId
* subjectId
* tumorLibraryId
* normalLibraryId
* tumorFastqListRowIds
* normalFastqListRowIds


```bash
# Globals

# EventBridge Globals
EVENT_BUS_NAME="OrcaBusMain"
EVENT_SOURCE="orcabus.manual"  # This is a manual pipeline trigger
EVENT_DETAIL_TYPE="WorkflowRunStateChange"

# Metadata globals
METADATA_API_URL="https://metadata.prod.umccr.org/api/v1/"
ORCABUS_TOKEN_SECRET_ID="orcabus/token-service-jwt"

# Payload globals
PAYLOAD_VERSION="2024.12.01"
READY_STATUS="READY"
WORKFLOW_NAME="tumor-normal"
WORKFLOW_VERSION="4.2.4"
ICAV2_VALIDATION_DATA_PROJECT_ID="7efd0cd5-a3b8-4ba3-b0be-7966eee29340"

# Input file parameters
TUMOR_LIBRARY_ID="SEQC-II_Tumor_50pc"
NORMAL_LIBRARY_ID="SEQC-II_Normal"

TUMOR_FASTQ_LIST_ROWS="$( \
  jq --null-input --raw-output \
    '
      [
        {
          "rgid": "SEQC-II_Tumor_50pc",
          "rglb": "SEQC-II_Tumor_50pc",
          "rgsm": "SEQC-II_Tumor_50pc",
          "lane": 1,
          "read1FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/fastq/SEQC-II_Tumor_50pc_R1.fastq.gz",
          "read2FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/fastq/SEQC-II_Tumor_50pc_R2.fastq.gz",
        }
      ]
    '
)"
NORMAL_FASTQ_LIST_ROWS="$( \
  jq --null-input --raw-output \
    '
      [
        {
          "rgid": "SEQC-II_Normal",
          "rglb": "SEQC-II_Normal",
          "rgsm": "SEQC-II_Normal",
          "lane": 1,
          "read1FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/fastq/SEQC-II_Normal_R1.fastq.gz",
          "read2FileUri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/fastq/SEQC-II_Normal_R2.fastq.gz",
        }
      ]
    '
)"
  
# Boolean parameters
ENABLE_DUPLICATE_MARKING="true"
ENABLE_CNV_SOMATIC="true"
ENABLE_HRD_SOMATIC="true"
ENABLE_SV_SOMATIC="true"
CNV_USE_SOMATIC_VC_BAF="true"
  
# Engine Parameters
OUTPUT_URI="s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/secondary-analysis/dragen-tumor-normal/4-2-4/"
LOGS_URI="s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/validation-data/wgs/SEQC50/secondary-analysis-logs/dragen-tumor-normal/4-2-4/"

# Tags
INDIVIDUAL_ID=""
SUBJECT_ID=""

# WRSC Level Functions
get_orcabus_token(){
  : '
  Required to make requests to the orcabus api
  '
  aws secretsmanager get-secret-value \
    --secret-id "${ORCABUS_TOKEN_SECRET_ID}" \
    --output json \
    --query SecretString | \
  jq --raw-output \
   'fromjson | .id_token'
}

get_linked_library_obj(){
  : '
  Given a library id, return library id and orcabus id 
  '
  local library_id="${1}"
  
  if ! orcabus_results="$( \
    curl --fail-with-body --silent --location --show-error \
      --header "Authorization: Bearer $(get_orcabus_token)" \
      --url "${METADATA_API_URL}library/?libraryId=${library_id}" 2>/dev/null \
  )"; then 
    jq --raw-output --null-input \
    '
      null
    '
  else 
    jq --raw-output \
      --exit-status \
      '
        if (.results | length) == 1 then
          {
            "libraryId": .libraryId,
            "orcabusId": .orcabusId
          } | 
          # Remove empty / null values
          with_entries(select(.value != "" and .value != null))
        else 
          null
        end
      ' <<< "${orcabus_results}"
  fi
}

generate_portal_run_id(){
  : '
  Generate a portal run id in the following format
  YYYYMMDD<8 digit random hexadecimal>
  '
  echo "$(date --utc +%Y%m%d)$(uuidgen | cut -c1-8)"
}

# Input level functions
get_fastq_list_row_ids(){
  : '
  Given an array of fastq files, return a list of fastq list row ids
  '
  local fastq_list_rows_json_str="${1}"
  
  jq --raw-output \
    '
      map(.rgid)
    ' <<< "${fastq_list_rows_json_str}"
}

generate_workflow_run_name(){
  : '
  Generate a name for the workflow run
  Replace any periods in the workflow version with hyphens
  '
  local portal_run_id="${1}"
  
  echo "umccr--automated--${WORKFLOW_NAME}--${WORKFLOW_VERSION//./-}--${portal_run_id}"
}

# Part 1 - Get the portal run id
portal_run_id="$(generate_portal_run_id)"

# Part 1 - Generate the data template
inputs_json_str="$( \
  jq --raw-output --null-input \
    --argjson enable_duplicate_marking "${ENABLE_DUPLICATE_MARKING}" \
    --argjson enable_cnv_somatic "${ENABLE_CNV_SOMATIC}" \
    --argjson enable_hrd_somatic "${ENABLE_HRD_SOMATIC}" \
    --argjson enable_sv_somatic "${ENABLE_SV_SOMATIC}" \
    --argjson cnv_use_somatic_vc_baf "${CNV_USE_SOMATIC_VC_BAF}" \
    --arg tumor_library_id "${TUMOR_LIBRARY_ID}" \
    --arg normal_library_id "${NORMAL_LIBRARY_ID}" \
    --argjson tumor_fastq_list_rows "${TUMOR_FASTQ_LIST_ROWS}" \
    --argjson normal_fastq_list_rows "${NORMAL_FASTQ_LIST_ROWS}" \
    '
      {
          # Boolean parameters
          "enableDuplicateMarking": $enable_duplicate_marking,
          "enableCnvSomatic": $enable_cnv_somatic,
          "enableHrdSomatic": $enable_hrd_somatic,
          "enableSvSomatic": $enable_sv_somatic,
          "cnvUseSomaticVcBaf": $cnv_use_somatic_vc_baf,
          # Str Parameters
          "outputPrefixSomatic": $tumor_library_id,
          "outputPrefixGermline": $normal_library_id,
          # File Parameters:
          "tumorFastqListRows": $tumor_fastq_list_rows,
          "fastqListRows": $normal_fastq_list_rows
      }
    '
)"

engine_parameters_json_str="$( \
  jq --raw-output --null-input \
    --arg output_uri "${OUTPUT_URI}" \
    --arg logs_uri "${LOGS_URI}" \
    --arg project_id "${ICAV2_VALIDATION_DATA_PROJECT_ID}" \
    '
      {
        "outputUri": $output_uri,
        "logsUri": $logs_uri,
        "projectId": $project_id
      }
    '
)"

tags_json_str="$( \
  jq --raw-output --null-input \
    --arg individual_id "${INDIVIDUAL_ID}" \
    --arg subject_id "${SUBJECT_ID}" \
    --arg tumor_library_id "${TUMOR_LIBRARY_ID}" \
    --arg normal_library_id "${NORMAL_LIBRARY_ID}" \
    --argjson tumor_fastq_list_row_ids "$(get_fastq_list_row_ids "${TUMOR_FASTQ_LIST_ROWS}")" \
    --argjson normal_fastq_list_row_ids "$(get_fastq_list_row_ids "${NORMAL_FASTQ_LIST_ROWS}")" \
    '
      {
        "individualId": $individual_id,
        "subjectId": $subject_id,
        "tumorLibraryId": $tumor_library_id,
        "normalLibraryId": $normal_library_id,
        "tumorFastqListRowIds": $tumor_fastq_list_row_ids,
        "normalFastqListRowIds": $normal_fastq_list_row_ids
      } |
      # Remove empty / null values 
      with_entries(select(.value != "" and .value != null))
    '
)"
 
data_json_str="$( \
  jq --raw-output --null-input \
    --argjson inputs "${inputs_json_str}" \
    --argjson engine_parameters "${engine_parameters_json_str}" \
    --argjson tags "${tags_json_str}" \
    '
      {
        "inputs": $inputs,
        "engineParameters": $engine_parameters,
        "tags": $tags
      }
    ' \
)"
  
payload_json_str="$( \
  jq --raw-output --null-input \
    --arg payload_version "${PAYLOAD_VERSION}" \
    --argjson data "${data_json_str}" \
    '
      {
        "version": $payload_version,
        "data": $data
      }
    ' \
)"
  
# Generate the workflow run state change ready event payload
workflow_run_state_change_event_json_str="$( \
  jq --raw-output --null-input \
    --argjson tumor_linked_library "$(get_linked_library_obj "${TUMOR_LIBRARY_ID}")" \
    --argjson normal_linked_library "$(get_linked_library_obj "${NORMAL_LIBRARY_ID}")" \
    --argjson payload "${payload_json_str}" \
    --arg portal_run_id "${portal_run_id}" \
    --arg workflow_name "${WORKFLOW_NAME}" \
    --arg workflow_version "${WORKFLOW_VERSION}" \
    --arg workflow_run_name "$(generate_workflow_run_name "${portal_run_id}")" \
    --arg ready_status "${READY_STATUS}" \
    '
      {
        "portalRunId": $portal_run_id,
        "timestamp": ( now | todate ),
        "status": $ready_status,
        "workflowName": $workflow_name,
        "workflowVersion": $workflow_version,
        "workflowRunName": $workflow_run_name,
        "linkedLibraries": ( 
          [
            $tumor_linked_library,
            $normal_linked_library
          ] | 
          # Remove empty / null values
          map(select(. != null))
        ),
        "payload": $payload
      }
    ' \
)"

# Launch the event
aws events put-events \
  --no-cli-pager \
  --cli-input-json "$( \
    jq --raw-output --compact-output --null-input \
      --arg event_bus_name "${EVENT_BUS_NAME}" \
      --arg event_source "${EVENT_SOURCE}" \
      --arg event_detail_type "${EVENT_DETAIL_TYPE}" \
      --argjson event_detail "${workflow_run_state_change_event_json_str}" \
      '
        {
          "Entries": [
            {
              "EventBusName": $event_bus_name,
              "Source": $event_source,
              "DetailType": $event_detail_type,
              "Detail": ( $event_detail | tojson)
            }
          ]
        }
      ' \
  )"
```



