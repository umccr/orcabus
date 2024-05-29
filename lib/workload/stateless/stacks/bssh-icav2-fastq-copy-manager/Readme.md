# BSSH Manager

<!-- TOC -->

* [BSSH Manager](#bssh-manager)
  * [Overview](#overview)
  * [Launch Inputs](#launch-inputs)
    * [Example Launch Event Payload](#example-launch-event-payload)
    * [Manual launching via the event bus](#manual-launching-via-the-event-bus-)
  * [Outputs](#outputs)
    * [Fastq List Rows Decompressed](#fastq-list-rows-decompressed)
    * [SampleSheet Decompressed](#samplesheet-decompressed)
  * [Lambdas in this directory](#lambdas-in-this-directory)
    * [Process BCLConvert Output](#process-bclconvert-output)
  * [AWS Secrets](#aws-secrets)
    * [External secrets required by the stack](#external-secrets-required-by-the-stack)
<!-- TOC -->

## Overview

The bssh manager runs performs the following logic:

Reads the bssh_output.json file from the BCLConvert run output folder

* Collects the fastq list csv file from the BCLConvert run output folder

* Read and return the fastq list rows as a list of dictionaries (gzip compressed / b64 encoded)

![](./images/step_functions_image.png)

## Inputs

* Statemachine is triggered by a WorkflowRunStateChange event from the workflowmanager:

An example event is shown below:

## Launch Inputs

In the top level of the payload we require the following values

* detail-type - The type of event, this should be set to workflowRunStateChange
* source - The source of the event, this should be set to orcabus.wfm

The AWSSSTep functions requires the following event detail information

* status - The status of the workflow run manager event (should be 'ready')
* workflowType - This must be set to bssh_fastq_copy
* workflowVersion - Not currently used, set to 1.0.0
* portalRunId - This is required to be set to a unique identifier for the run
* payload
  * refId: Not tracked by this service, only by the workflow run manager service
  * version: The service version, not currently used set to 2024.05.15
  * bsshProjectId: The project id of the BSSH managed ICAv2 project where the fastqs reside
  * bsshAnalysisId: The analysis id that ran BCLConvert for the BSSH managed ICAv2 project
  * outputUriPrefix: The output uri prefix for where these fastqs are copied to (we add the run id and portal run id onto the end)

* Statemachine is triggered by the following input: 
  * source 
    * project_id (the project in which BCLConvert was run), 
    * analysis_id (the analysis id), and a 
    * portal_run_id (a unique identifier to provide a unique location for the outputs)

### Example Launch Event Payload

An example of a launch event can be seen below

<details>

<summary>Click to expand!</summary>

```json5
{
  "DetailType": "WorkflowRunStateChange",
  "EventBusName": "OrcaBusMain",
  "Source": "orcabus.workflowmanager",
  "Detail": {
    "portalRunId": "20240528da604011",
    "timestamp": "2024-05-28T22:51:22Z",
    "status": "ready",
    "workflowName": "bsshFastqCopy",
    "workflowVersion": "2024.05.24",
    "payload": {
      "refId": "018fc166-a8d2-772a-92e2-1668ee1034d7",
      "version": "2024.05.24",
      "data": {
        "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/240229_A00130_0288_BH5HM2DSXC/20240528da604011/",
        "analysisId": "01bd501f-dde6-42b5-b281-5de60e43e1d7",
        "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
        "projectId": "b23fb516-d852-4985-adcc-831c12e8cd22"
      }
    }
  }
}
```

</details>

# The important components of the inputs are:

* outputUri - Where the data will be placed
* analysisId - (the analysis id to query in order to collect the location of the fastq list rows csv),
* instrumentRunId - (not used by the step function but parsed for the completion event to tie the fastq list rows to an instrument run id),
* projectId - The bssh project id that ran the analysis id.  
  * This is also the project context that the copy batch data API calls need to be run in.  




</details>


### Manual launching via the event bus 

> A scripted example

<details>

<summary>Click to expand!</summary>

```bash
# Workflow Input
bssh_project_id="b23fb516-d852-4985-adcc-831c12e8cd22"     # BSSH-trial
output_project_id="7595e8f2-32d3-4c76-a324-c6a85dae87b5"   # Trial
bssh_analysis_id="544654e7-c198-466f-b981-44b5364ee4d8"    # The BCLConvert Analysis ID triggered by BSSH
output_uri_prefix="icav2://${output_project_id}/ilmn_primary/"

# Event metadata
portal_run_id="$(date --utc +%Y%m%d)$(xxd -l 4 -c 4 -p < /dev/random)"
utc_time="$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')"

# Generate the input payload
input_payload="$( \
  jq --null-input --raw-output \
    --arg project_id "${project_id}" \
    --arg bssh_project_id "${bssh_project_id}" \
    --arg bssh_analysis_id "${bssh_analysis_id}" \
    --arg output_uri_prefix "${output_uri_prefix}" \
    '
      {
        "refId": null,
        "version": "0.1.0",
        "bsshProjectId": $bssh_project_id,
        "bsshAnalysisId": $bssh_analysis_id,
        "outputUriPrefix": $output_uri_prefix
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
        "workflowType": "bssh_fastq_copy",
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
            "DetailType": "workflowRunStateChange",
            "Source": "orcabus.wfm",
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
```

</details>


## Outputs

We output the fastq list rows in b64gz format.
This is a gzip compressed, base64 encoded string of the fastq list rows dictionary.

```json5
{
  "outputs": {
    "instrumentRunId": "231116_A01052_0172_BHVLM5DSX7",
    // pragma: allowlist secret 
    "fastq_list_rows_b64gz": "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",
  }
}
```

Note that the fastqListRowsB64gz and samplesheetB64gz are gzip compressed and base64 encoded. 

To decode these see the headers below 

### Fastq List Rows Decompressed

1. Get the output directory of the underlying BCLConvert run
5. Collect the fastq list csv file from the BCLConvert run output folder

<summary>Click to expand!</summary>

## SSM Parameters

### External SSM Parameters required by this CDK stack

```json5
[
  {
    "RGID": "GACTGAGTAG.CACTATCAAC.1",
    "RGSM": "L2301368",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301368/L2301368_S1_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301368/L2301368_S1_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "AGTCAGACGA.TGTCGCTGGT.1",
    "RGSM": "L2301369",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301369/L2301369_S2_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301369/L2301369_S2_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "CCGTATGTTC.ACAGTGTATG.1",
    "RGSM": "L2301370",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301370/L2301370_S3_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301370/L2301370_S3_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "GAGTCATAGG.AGCGCCACAC.1",
    "RGSM": "L2301371",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301371/L2301371_S4_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301371/L2301371_S4_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "CTTGCCATTA.CCTTCGTGAT.1",
    "RGSM": "L2301372",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301372/L2301372_S5_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301372/L2301372_S5_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "GAAGCGGCAC.AGTAGAGCCG.1",
    "RGSM": "L2301373",
    "RGLB": "UnknownLibrary",
    "Lane": 1,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301373/L2301373_S6_L001_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_1/L2301373/L2301373_S6_L001_R2_001.fastq.gz"
  },
  {
    "RGID": "AGGTCAGATA.TATCTTGTAG.2",
    "RGSM": "L2301346_rerun",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301346_rerun/L2301346_rerun_S7_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301346_rerun/L2301346_rerun_S7_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "CGTCTCATAT.AGCTACTATA.2",
    "RGSM": "L2301347_rerun",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301347_rerun/L2301347_rerun_S8_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301347_rerun/L2301347_rerun_S8_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "ATTCCATAAG.CCACCAGGCA.2",
    "RGSM": "L2301348_rerun",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301348_rerun/L2301348_rerun_S9_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301348_rerun/L2301348_rerun_S9_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "GACGAGATTA.AGGATAATGT.2",
    "RGSM": "L2301349_rerun",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301349_rerun/L2301349_rerun_S10_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301349_rerun/L2301349_rerun_S10_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "AACATCGCGC.ACAAGTGGAC.2",
    "RGSM": "L2301350_rerun",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301350_rerun/L2301350_rerun_S11_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301350_rerun/L2301350_rerun_S11_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "TCCATTGCCG.TCGTGCATTC.2",
    "RGSM": "L2301374",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301374/L2301374_S12_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301374/L2301374_S12_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "CGGTTACGGC.CTATAGTCTT.2",
    "RGSM": "L2301375",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301375/L2301375_S13_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301375/L2301375_S13_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "GAGCAACA.GCATCTAC.2",
    "RGSM": "L2301385",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301385/L2301385_S14_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301385/L2301385_S14_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "AAGATTGA.GTGGTTCG.2",
    "RGSM": "L2301387",
    "RGLB": "UnknownLibrary",
    "Lane": 2,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301387/L2301387_S15_L002_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_2/L2301387/L2301387_S15_L002_R2_001.fastq.gz"
  },
  {
    "RGID": "CAGTGACG.GAGCGGTA.3",
    "RGSM": "L2301386",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301386/L2301386_S16_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301386/L2301386_S16_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "GTGTGTTT.GAACAATA.3",
    "RGSM": "L2301388",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301388/L2301388_S17_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301388/L2301388_S17_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "TGCGGCGT.TACCGAGG.3",
    "RGSM": "L2301389",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301389/L2301389_S18_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301389/L2301389_S18_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "CATAATAC.CGTTAGAA.3",
    "RGSM": "L2301390",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301390/L2301390_S19_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301390/L2301390_S19_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "GATCTATC.AGCCTCAT.3",
    "RGSM": "L2301391",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301391/L2301391_S20_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301391/L2301391_S20_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "AGCTCGCT.GATTCTGC.3",
    "RGSM": "L2301392",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301392/L2301392_S21_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301392/L2301392_S21_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "CGGAACTG.TCGTAGTG.3",
    "RGSM": "L2301393",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301393/L2301393_S22_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301393/L2301393_S22_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "TTGCCTAG.TAAGTGGT.3",
    "RGSM": "L2301395",
    "RGLB": "UnknownLibrary",
    "Lane": 3,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301395/L2301395_S23_L003_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_3/L2301395/L2301395_S23_L003_R2_001.fastq.gz"
  },
  {
    "RGID": "CCGCGGTT.CTAGCGCT.4",
    "RGSM": "L2301321",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301321/L2301321_S24_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301321/L2301321_S24_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TTATAACC.TCGATATC.4",
    "RGSM": "L2301322",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301322/L2301322_S25_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301322/L2301322_S25_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "GGACTTGG.CGTCTGCG.4",
    "RGSM": "L2301323",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301323/L2301323_S26_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301323/L2301323_S26_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "AAGTCCAA.TACTCATA.4",
    "RGSM": "L2301324",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301324/L2301324_S27_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301324/L2301324_S27_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "ATCCACTG.ACGCACCT.4",
    "RGSM": "L2301325",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301325/L2301325_S28_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301325/L2301325_S28_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "GCTTGTCA.GTATGTTC.4",
    "RGSM": "L2301326",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301326/L2301326_S29_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301326/L2301326_S29_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "CAAGCTAG.CGCTATGT.4",
    "RGSM": "L2301327",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301327/L2301327_S30_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301327/L2301327_S30_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TGGATCGA.TATCGCAC.4",
    "RGSM": "L2301328",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301328/L2301328_S31_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301328/L2301328_S31_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "AGTTCAGG.TCTGTTGG.4",
    "RGSM": "L2301329",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301329/L2301329_S32_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301329/L2301329_S32_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "GACCTGAA.CTCACCAA.4",
    "RGSM": "L2301330",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301330/L2301330_S33_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301330/L2301330_S33_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TCTCTACT.GAACCGCG.4",
    "RGSM": "L2301331",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301331/L2301331_S34_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301331/L2301331_S34_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "CTCTCGTC.AGGTTATA.4",
    "RGSM": "L2301332",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301332/L2301332_S35_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301332/L2301332_S35_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TAATACAG.GTGAATAT.4",
    "RGSM": "L2301333",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301333/L2301333_S36_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301333/L2301333_S36_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "CGGCGTGA.ACAGGCGC.4",
    "RGSM": "L2301334",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301334/L2301334_S37_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301334/L2301334_S37_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "ATGTAAGT.CATAGAGT.4",
    "RGSM": "L2301335",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301335/L2301335_S38_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301335/L2301335_S38_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "AATCCGGA.AACTGTAG.4",
    "RGSM": "L2301344",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301344/L2301344_S39_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301344/L2301344_S39_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TGCGGCGT.TACCGAGG.4",
    "RGSM": "L2301389",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301389/L2301389_S18_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301389/L2301389_S18_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "GATCTATC.AGCCTCAT.4",
    "RGSM": "L2301391",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301391/L2301391_S20_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301391/L2301391_S20_L004_R2_001.fastq.gz"
  },
  {
    "RGID": "TAAGGTCA.CTACGACA.4",
    "RGSM": "L2301394",
    "RGLB": "UnknownLibrary",
    "Lane": 4,
    "Read1FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301394/L2301394_S40_L004_R1_001.fastq.gz",
    "Read2FileURI": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307abcd7890/Samples/Lane_4/L2301394/L2301394_S40_L004_R2_001.fastq.gz"
  }
]
```
/icav2/umccr-prod/service-user-trial-jwt-token-secret-arn
```

</details>

## Lambdas in this directory

All lambdas run on python 3.11 or higher.

### Process BCLConvert Output

1. Get the output directory of the underlying BCLConvert run
2. Collect the bssh_output.json file from the BCLConvert run output folder
3. Collect the basespace run id from the bssh output json
4. Collect the run id from the run info xml
5. Collect the fastq list csv file from the BCLConvert run output folder


## AWS Secrets

### External secrets required by the stack

* ICAv2JWTKey-umccr-prod-service-trial # Development
* ICAv2JWTKey-umccr-prod-service-staging # Staging
* ICAv2JWTKey-umccr-prod-service-prod # Production