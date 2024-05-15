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

* Collects the basespace run id from the bssh output json

* Collects the run id from the run info xml

* Collects the fastq list csv file from the BCLConvert run output folder

* Read and return the fastq list rows as a list of dictionaries (gzip compressed / b64 encoded)

* Collects the samplesheet path from the BCLConvert run output folder (as we might need this to go into the cttso directories)

* Read and return the samplesheet as a dictionary (via the v2-samplesheet-maker package) (gzip compressed / b64 encoded)

* Return a manifest of icav2 uris where each key represents a ICAv2 data uri (file) and the value is a list of icav2 uris where each uri is a destination for a given file.

![](./images/step_functions_image.png)

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
    "version": "0",
    "id": "2ce3c70c-e757-6246-5783-a83543d87ea7",
    "detail-type": "workflowRunStateChange",
    "source": "orcabus.wfm",
    "account": "843407916570",
    "time": "2024-05-10T08:25:12Z",
    "region": "ap-southeast-2",
    "resources": [],
    "detail": {
        "status": "ready",
        "workflowType": "bssh_fastq_copy",
        "workflowVersion": "1.3.1--1.2.1",
        "portalRunId": "20240510abcd0030",
        "payload": {
            refId: null,
            version: "2024.05.15",
            bsshProjectId: "b23fb516-d852-4985-adcc-831c12e8cd22",
            bsshAnalysisId: "544654e7-c198-466f-b981-44b5364ee4d8",
            outputUriPrefix: "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/"
        }
    }
}
```

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
        "bsshProjectId": "${bssh_project_id}"
        "bsshAnalysisId": "${bssh_analysis_id}"
        "outputUriPrefix": "${output_uri_prefix}"
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

// Add actual outputs here

```json5
{
  "outputs": {
    "instrumentRunId": "231116_A01052_0172_BHVLM5DSX7",
    "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/231116_A01052_0172_BHVLM5DSX7/20240307abcd7890/",
    "fastqListRowsB64gz": "H4sIAAAAAAAAA92c32/bNhDH3/NXGHluZJGURKlvLItxBdyXiC0GFIWgJO5gLPE6dz+wDfvfd0dD9NKRDtmnHFEEPSduke99jsfj8eQPF6vV3/C1Wl1emzevL1+uLo3S1ihjlak0mMpqpXTFLl8sbxvf4ts2XNRMdP3p+5tX+P13+5/2P/+x3+xuDvPhz+Wnm3m/hZ+y5c3b+Y59t7vfvrt+g/9odzv/zl+u17Id2m3/iV8JfieumlvZXc2CN1e33dy3d/O2lzftenf/sJ8+H3YP8P+vec3FmgvGWDepmtUtn2om+fTq+/ebt+3r8Qe5Fl3HunbAtza1qOV8c3sn+6Fej/PD5/vtlzX+chNbL4q8MY1s2tQ1m67ZBH9Vn+Yvv/5S/fjX5X9UcEIq+GMVIOKfF//nD+i1giAwqrJgGogGY6P8h+L4D96YRk6Wf0hFGn+tYe0DeasrBYFg3asYf1mXxl/W3phGQZV/UEUaf+MSAKR/UykDyx82gXj+l6w4/idjGhuy/EMqEte/tQjdWlVpsCEbGBXN/5IXx597YxpbsvxDKlLXPy57g4veVYHwSsfzvyiOv/DGNHZk+YdUpNZ/xwIQ1j8W/9a6owAP82+66bA9/LbPigL+fKNgWTaLrq9eTqNEX3JCEZGsKHF3gOBw5YHF6sC6A6KKRocsNDrkY1/KxZc92eh4SlFi7oB6AYMDewewgUAagX0kGh19odHRP/Zlv/hyIBsdTylKrSy0wY0FEgYEBoYJ7C3R6BgKjY7hsS+HxZesJhseT0pKzB5w0sSGk3GdB2w9QMTE4qOty4yPRddXL8GZjGp8PC0pLT7c3mLdccQdS/FVND5kU1pkyMYb4DpONRrCMlKrTwO7B55OK1d4YjEa3UFkW1wEtN4A1wmyERCUkdydxPsoVeHqx/NHjH5fHP2+9Qa4raFKPywjtULA8tEAfbyUgk0gSl8WR196A9zWkqUflJGY/bEkhOxfGdehhGOEiNDvsuiL50t/aeP1nTfAba6hJwjRPy8jMfNb/APbvcH8r87Qz5tJoEC/9wa4TZKlH5SRWPu7OwljK9jysYtgovTzJhIo0B+8AW7rydIPykjN/NgsgmJPY/0PCSBGf8ibRyBAf6i9AW4bqNIPy0it+a2bQ8MbB3f5EKWfN41AgT7zxjTymiz9oIzU+0jtptAqLP017ANR+nmzCBToc2+A2xhZ+kEZyR0fhQOpruOH9X+Uft4kAgX6JwPcxsnSD8pIrPqw24vjB/Z4HRDP/HndHgr0W2+A2wRZ+kEZyZOoruGLvV7jtoAmTJ/n7fvN86W/9MY58wa4zTXJGkL0z8tIXftY9GuNmV+58i9GP2/fp0CfewPc1pKlH5SRWPPjYyiQ8Ss3cASrP0o/b9+nQF94A9zWkaUflJHc58fLXpxAPE6bRenn3fJSoH8ywG2SLP2gjNQpMhweg1JfaRxDPrPv51V9FOi33gC39WTpB2UkZn43cow3vMtjSDH6ebc8FOh33gC3DWTpB2WkdnrdWDHu+9rxj9LPu+GlQF96YxpFTZZ+UEbqLQ/2es3xyQP3CEqMft4dHwX6vTfAbYws/aCM5CeP8ckT7PVh4jfxmj/vjo8C/cEb4DZOln5QRvJ0OH7wgKqw4nfFf4S+yLvjI0Bf1N4Atwmq9MMyUmd73TTfcbpDnznvi+J6fYJ5A9xGttcXlpH6zDHe8bkbXuP6flH6xfX6BPcGuI1sry8sI3Htu9kOqPlxvM89WhijX1yvTwhvgNvI9vrCMpJveN1nDLhPG3EP/8ToF9frEycD3Ea21xeWkdrrM+5ut3IfOaLi531RXK9PtN4At5Ht9YVlpPb5rcYJj8rNeGDbJ0K/KW7tNycD3Ea21xeW8a0zvRH6mTO9BOgHhmEp0g/L+Napzgj9zKlOAvQD45AU6YdlJNf87nNmcLYH1r6OnviG4jL/cDKmsaFLPygjQP/i48W/C1okTmdUAAA=", /* pragma: allowlist secret */
    "samplesheetB64gz": "H4sIAAAAAAAAA91b227bOBB9z1cU3tek0M2WlD5pVUAo0M0uGvahWCwGsq20Qm3ZlZV0i0X/fTmUGcvlULQVxmiNIAEcUuKZIefqw/8uXrwYfSryeVGPrl/8xz/xz3flooC7Vb3MG3go6k25qvigd9mO1vcVVPmy4P8asc2X6uqmmL67STzfdV3/6o+3RXHL3oE7uVk9eP5o+1BZbZr6fllUDTTf1uJZPp7fFl9GfMJ3nDWqOYzNDgV+BBdm32aLAv/tjt3LzohHjZTVvPh37yFnb6T7kPO48HS2mK0qLmkDm6JpyupjB8ayrMrl/RKaulwuizmIxRdF9bH5xCf548v9afk8XzdFDSv+ukW+xilyRr75DJtPK76KlPTx6c3qrvma10VH3aPgpfcyHFEg53mT8xl/i2dbmHzCIq9Qr1tV4Evz5ZpvZDnHt731fMf1J9HocVhoBIeyJGVZkrEk+2HQw9GUjyYsTZJ0N4rC1eW82Glz9D68cT+4gf/qjeuIX/mP3VNSNe3GinezjKX8hy+Q8HX4Mkwz3dNNF7O/Xw5QRUyogmshTbg+soRSBS6fcRAZOy9VhA6hijTlJ4KvwlJKFXzJjIkJZ6YKlzQQPBbcPkgDSTJ+KHDhMzOQ0KNOBWMoLF+B9BV8mB+bLDk3A/HJU4E7n+3te/dU8PPCJ6S/noF4faoIJvzNPAUgnWfrPemzgUGEsf0ocxYKCbUKScUyfBGm8RtMxNbkzBQS6U8Idw+oD02mwZfm54db1JkpJNYqRKQamc6dcl2gstgvmG/0KmTs6E+IeDdGVE3WgWlH9guG2l6FhAGhCmEqbD+CdNwpxlmccG6qGJOOlOehCQZb0m/gwgjhzMwkolSBOQUaCaWITCxoMI4PvFp+9Sa68do/+PEJEEPShtGj0SUUWi/miFYh+r0QJ9SBQjeS0JaVibTOEJXtQiSrcoY/jEwdMjwBpsTBLkSqWmYi/81IiPwYYmg74UbHZBUrAiidoqfoVLgqTwiRri6Z6LBockSRQZ4QIlX1YaqKnQ/6LHJ7Zpldp9MPkarG+ElMsI+li5Vo8CeESLluEcw1XTbWJjZ2Nzrog+hRZzFNhe8jNxqh7x+CZ4dInUURW7lz0Wx0sm9Kzw6R7AxgR5XR3SJRE2aWA2A/RCq5xOPG80tNpd5WrSeESJlLggA1Fs1DNxaLpzyLVBqRiY6GJhlTuqfPDpFKxrBi0jkdtGZjdWkXIpXpYEHHdC13UQ1aTmn7IWq+F8DWlia64D5bznR6IfpUppOhPWS0RaM971v7s0OkoosojRJdGpGI4HNCiHR/GzMdXTKWMWO7zi5EKrq0CS1t0VjV7Pcbnx0iFV3asoC26ES0+Czni/0Q6eiSiZyLNJdE9O5PqMWAjtE8AmYaLWJkNPXSrUL8OSrAXog/R3nVD5Hs9CXtVyearJtr0dAS10Pkf//BJ0ezxep+TtAbPhZVUedNMe9SD5yX/Ge74vbJr6v6891i9RWHy1n++BmkzrsEhXW5Lhal0Mbovq6uy8WS/5nl13LgenoX+9Px7O5qNvXCq2B+l19FwaS4ymfzSTF1Ijef5b/9Pluk2zc+BOBBhw3RgqKJEIZiZ1FO67z+9shhkTNAFj+gVjrymXVdrOFz2XQJMLfsHX0eDBWNBocHssIBtZyxhsM34vBBljGg1izWcARGHAHIWgXUwsQajrERxxhkQQJq9WENx8SIYwKy6gC1xLCGIzTiCEGWFqDWEdZwREYcEcj6AdRiwRqO2IgjBlkkgFoR2MLRzfxpHL4DshIANe23hsPoT30XZLoPam5vDYfRn/oeyJwe1ATeGg6jP/V9kIk7qFm6NRxGf+oHILNzUFNxaziM/tRHf9qm4KDm27ZwBEZ9BBhf2jwb1KTaGg6FNaNBs50HOy4NUMQZLa5Zw27/fPAOB6awVzTAtvNgx2kBisBiD5jCItEAi6TGHrklQBFJ7AFT2BwaYNt5sON4AEXosAZMZVXQwOQ82HEtgCJWWAM2MQbxSQQ7EjJQjGN7YIyRfCIi+ZYGDBTn1xqY0BjOQwd2RFygWLf2wBhjeujCjgoLFO/VHhhjYA8xsEsyKlDMU3tgjNE99GFHBwWK+2kPjDGkhQHsuENAEYXsgTHG+XAMO/YOUFQda2AiI5hoDJI/AypZRgukveByOA5jERdNQDJQQKWbWMNhLOKiECRZB1RmjjUcRv8fRSDpLqByW6zhMLr+KAbZ0QS1fdmXDN7k1epgILHR7ccOSOYKqDQVe0CMLj9Gl982UEHtltoDYnT3sQeShQIq5cQeEKOrj32QXBNQiSX2gBjdfByAbByD2iW2B8ToVeMxSGoLqDyWA4FcyEZ1s1mNHWdBtKqPYWceyM38YfK0+JQ/lKt7vAs5wgt/csKhlwB7rvgdxUi9kH1uqY2DO91qpbmdJK9dvr7pnpIfOZ5PuMxRhtBesmzhvH/9l+M43e9Yx+T4wXWXUqkOE+z4SxmkYL5BMP8Jle7AHTv6cgUpWGAQLHhCpTxMsOMvSZCCjQ2CjZ9QaQ/csaMvO5CCTQyCTQZV6geI5JJ7deRdYlKk2CBSPKjeHybS8XeCKZFcp18kPn6oSN2uwTCRjr/bS4rkGkTSfE9u6D0MPXjH3tElRTLEK3dYB2PgLh1915YUyRCp3MMjVbcPMnSXjr0zS4pkiFHu4TGq200Z5sSPv6ZFimSITu7h0anbkxmaIh173YoUyRCX3Ekn9b/4fvE/hhiak4tEAAA=",  /* pragma: allowlist secret */
    "basespaceRunId": 3661659
  }
}
```

Note that the fastqListRowsB64gz and samplesheetB64gz are gzip compressed and base64 encoded. 

To decode these see the headers below 

### Fastq List Rows Decompressed

<details>

<summary>Click to expand!</summary>

```bash
fastq_list_rows_base64="H4sIAAAAAAAAA92c32/bNhDH3/NXGHluZJGURKlvLItxBdyXiC0GFIWgJO5gLPE6dz+wDfvfd0dD9NKRDtmnHFEEPSduke99jsfj8eQPF6vV3/C1Wl1emzevL1+uLo3S1ihjlak0mMpqpXTFLl8sbxvf4ts2XNRMdP3p+5tX+P13+5/2P/+x3+xuDvPhz+Wnm3m/hZ+y5c3b+Y59t7vfvrt+g/9odzv/zl+u17Id2m3/iV8JfieumlvZXc2CN1e33dy3d/O2lzftenf/sJ8+H3YP8P+vec3FmgvGWDepmtUtn2om+fTq+/ebt+3r8Qe5Fl3HunbAtza1qOV8c3sn+6Fej/PD5/vtlzX+chNbL4q8MY1s2tQ1m67ZBH9Vn+Yvv/5S/fjX5X9UcEIq+GMVIOKfF//nD+i1giAwqrJgGogGY6P8h+L4D96YRk6Wf0hFGn+tYe0DeasrBYFg3asYf1mXxl/W3phGQZV/UEUaf+MSAKR/UykDyx82gXj+l6w4/idjGhuy/EMqEte/tQjdWlVpsCEbGBXN/5IXx597YxpbsvxDKlLXPy57g4veVYHwSsfzvyiOv/DGNHZk+YdUpNZ/xwIQ1j8W/9a6owAP82+66bA9/LbPigL+fKNgWTaLrq9eTqNEX3JCEZGsKHF3gOBw5YHF6sC6A6KKRocsNDrkY1/KxZc92eh4SlFi7oB6AYMDewewgUAagX0kGh19odHRP/Zlv/hyIBsdTylKrSy0wY0FEgYEBoYJ7C3R6BgKjY7hsS+HxZesJhseT0pKzB5w0sSGk3GdB2w9QMTE4qOty4yPRddXL8GZjGp8PC0pLT7c3mLdccQdS/FVND5kU1pkyMYb4DpONRrCMlKrTwO7B55OK1d4YjEa3UFkW1wEtN4A1wmyERCUkdydxPsoVeHqx/NHjH5fHP2+9Qa4raFKPywjtULA8tEAfbyUgk0gSl8WR196A9zWkqUflJGY/bEkhOxfGdehhGOEiNDvsuiL50t/aeP1nTfAba6hJwjRPy8jMfNb/APbvcH8r87Qz5tJoEC/9wa4TZKlH5SRWPu7OwljK9jysYtgovTzJhIo0B+8AW7rydIPykjN/NgsgmJPY/0PCSBGf8ibRyBAf6i9AW4bqNIPy0it+a2bQ8MbB3f5EKWfN41AgT7zxjTymiz9oIzU+0jtptAqLP017ANR+nmzCBToc2+A2xhZ+kEZyR0fhQOpruOH9X+Uft4kAgX6JwPcxsnSD8pIrPqw24vjB/Z4HRDP/HndHgr0W2+A2wRZ+kEZyZOoruGLvV7jtoAmTJ/n7fvN86W/9MY58wa4zTXJGkL0z8tIXftY9GuNmV+58i9GP2/fp0CfewPc1pKlH5SRWPPjYyiQ8Ss3cASrP0o/b9+nQF94A9zWkaUflJHc58fLXpxAPE6bRenn3fJSoH8ywG2SLP2gjNQpMhweg1JfaRxDPrPv51V9FOi33gC39WTpB2UkZn43cow3vMtjSDH6ebc8FOh33gC3DWTpB2WkdnrdWDHu+9rxj9LPu+GlQF96YxpFTZZ+UEbqLQ/2es3xyQP3CEqMft4dHwX6vTfAbYws/aCM5CeP8ckT7PVh4jfxmj/vjo8C/cEb4DZOln5QRvJ0OH7wgKqw4nfFf4S+yLvjI0Bf1N4Atwmq9MMyUmd73TTfcbpDnznvi+J6fYJ5A9xGttcXlpH6zDHe8bkbXuP6flH6xfX6BPcGuI1sry8sI3Htu9kOqPlxvM89WhijX1yvTwhvgNvI9vrCMpJveN1nDLhPG3EP/8ToF9frEycD3Ea21xeWkdrrM+5ut3IfOaLi531RXK9PtN4At5Ht9YVlpPb5rcYJj8rNeGDbJ0K/KW7tNycD3Ea21xeW8a0zvRH6mTO9BOgHhmEp0g/L+Napzgj9zKlOAvQD45AU6YdlJNf87nNmcLYH1r6OnviG4jL/cDKmsaFLPygjQP/i48W/C1okTmdUAAA="  # pragma: allowlist secret
base64 -d <<< "${fastq_list_rows_base64}" | \
gunzip | \
jq --raw-output
```

Yields

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

</details>

### SampleSheet Decompressed

<details>

<summary>Click to expand!</summary>

```bash
samplesheet_b64gz="H4sIAAAAAAAAA91b227bOBB9z1cU3tek0M2WlD5pVUAo0M0uGvahWCwGsq20Qm3ZlZV0i0X/fTmUGcvlULQVxmiNIAEcUuKZIefqw/8uXrwYfSryeVGPrl/8xz/xz3flooC7Vb3MG3go6k25qvigd9mO1vcVVPmy4P8asc2X6uqmmL67STzfdV3/6o+3RXHL3oE7uVk9eP5o+1BZbZr6fllUDTTf1uJZPp7fFl9GfMJ3nDWqOYzNDgV+BBdm32aLAv/tjt3LzohHjZTVvPh37yFnb6T7kPO48HS2mK0qLmkDm6JpyupjB8ayrMrl/RKaulwuizmIxRdF9bH5xCf548v9afk8XzdFDSv+ukW+xilyRr75DJtPK76KlPTx6c3qrvma10VH3aPgpfcyHFEg53mT8xl/i2dbmHzCIq9Qr1tV4Evz5ZpvZDnHt731fMf1J9HocVhoBIeyJGVZkrEk+2HQw9GUjyYsTZJ0N4rC1eW82Glz9D68cT+4gf/qjeuIX/mP3VNSNe3GinezjKX8hy+Q8HX4Mkwz3dNNF7O/Xw5QRUyogmshTbg+soRSBS6fcRAZOy9VhA6hijTlJ4KvwlJKFXzJjIkJZ6YKlzQQPBbcPkgDSTJ+KHDhMzOQ0KNOBWMoLF+B9BV8mB+bLDk3A/HJU4E7n+3te/dU8PPCJ6S/noF4faoIJvzNPAUgnWfrPemzgUGEsf0ocxYKCbUKScUyfBGm8RtMxNbkzBQS6U8Idw+oD02mwZfm54db1JkpJNYqRKQamc6dcl2gstgvmG/0KmTs6E+IeDdGVE3WgWlH9guG2l6FhAGhCmEqbD+CdNwpxlmccG6qGJOOlOehCQZb0m/gwgjhzMwkolSBOQUaCaWITCxoMI4PvFp+9Sa68do/+PEJEEPShtGj0SUUWi/miFYh+r0QJ9SBQjeS0JaVibTOEJXtQiSrcoY/jEwdMjwBpsTBLkSqWmYi/81IiPwYYmg74UbHZBUrAiidoqfoVLgqTwiRri6Z6LBockSRQZ4QIlX1YaqKnQ/6LHJ7Zpldp9MPkarG+ElMsI+li5Vo8CeESLluEcw1XTbWJjZ2Nzrog+hRZzFNhe8jNxqh7x+CZ4dInUURW7lz0Wx0sm9Kzw6R7AxgR5XR3SJRE2aWA2A/RCq5xOPG80tNpd5WrSeESJlLggA1Fs1DNxaLpzyLVBqRiY6GJhlTuqfPDpFKxrBi0jkdtGZjdWkXIpXpYEHHdC13UQ1aTmn7IWq+F8DWlia64D5bznR6IfpUppOhPWS0RaM971v7s0OkoosojRJdGpGI4HNCiHR/GzMdXTKWMWO7zi5EKrq0CS1t0VjV7Pcbnx0iFV3asoC26ES0+Czni/0Q6eiSiZyLNJdE9O5PqMWAjtE8AmYaLWJkNPXSrUL8OSrAXog/R3nVD5Hs9CXtVyearJtr0dAS10Pkf//BJ0ezxep+TtAbPhZVUedNMe9SD5yX/Ge74vbJr6v6891i9RWHy1n++BmkzrsEhXW5Lhal0Mbovq6uy8WS/5nl13LgenoX+9Px7O5qNvXCq2B+l19FwaS4ymfzSTF1Ijef5b/9Pluk2zc+BOBBhw3RgqKJEIZiZ1FO67z+9shhkTNAFj+gVjrymXVdrOFz2XQJMLfsHX0eDBWNBocHssIBtZyxhsM34vBBljGg1izWcARGHAHIWgXUwsQajrERxxhkQQJq9WENx8SIYwKy6gC1xLCGIzTiCEGWFqDWEdZwREYcEcj6AdRiwRqO2IgjBlkkgFoR2MLRzfxpHL4DshIANe23hsPoT30XZLoPam5vDYfRn/oeyJwe1ATeGg6jP/V9kIk7qFm6NRxGf+oHILNzUFNxaziM/tRHf9qm4KDm27ZwBEZ9BBhf2jwb1KTaGg6FNaNBs50HOy4NUMQZLa5Zw27/fPAOB6awVzTAtvNgx2kBisBiD5jCItEAi6TGHrklQBFJ7AFT2BwaYNt5sON4AEXosAZMZVXQwOQ82HEtgCJWWAM2MQbxSQQ7EjJQjGN7YIyRfCIi+ZYGDBTn1xqY0BjOQwd2RFygWLf2wBhjeujCjgoLFO/VHhhjYA8xsEsyKlDMU3tgjNE99GFHBwWK+2kPjDGkhQHsuENAEYXsgTHG+XAMO/YOUFQda2AiI5hoDJI/AypZRgukveByOA5jERdNQDJQQKWbWMNhLOKiECRZB1RmjjUcRv8fRSDpLqByW6zhMLr+KAbZ0QS1fdmXDN7k1epgILHR7ccOSOYKqDQVe0CMLj9Gl982UEHtltoDYnT3sQeShQIq5cQeEKOrj32QXBNQiSX2gBjdfByAbByD2iW2B8ToVeMxSGoLqDyWA4FcyEZ1s1mNHWdBtKqPYWceyM38YfK0+JQ/lKt7vAs5wgt/csKhlwB7rvgdxUi9kH1uqY2DO91qpbmdJK9dvr7pnpIfOZ5PuMxRhtBesmzhvH/9l+M43e9Yx+T4wXWXUqkOE+z4SxmkYL5BMP8Jle7AHTv6cgUpWGAQLHhCpTxMsOMvSZCCjQ2CjZ9QaQ/csaMvO5CCTQyCTQZV6geI5JJ7deRdYlKk2CBSPKjeHybS8XeCKZFcp18kPn6oSN2uwTCRjr/bS4rkGkTSfE9u6D0MPXjH3tElRTLEK3dYB2PgLh1915YUyRCp3MMjVbcPMnSXjr0zS4pkiFHu4TGq200Z5sSPv6ZFimSITu7h0anbkxmaIh173YoUyRCX3Ekn9b/4fvE/hhiak4tEAAA="  # pragma: allowlist secret
base64 -d <<< "${samplesheet_b64gz}" | \
gunzip | \
jq --raw-output | \
v2-samplesheet-maker - -
```

Yields

```
[Header]
FileFormatVersion,2
RunName,Tsqn-NebRNA231113-MLeeSTR_16Nov23
InstrumentType,NovaSeq

[Reads]
Read1Cycles,151
Read2Cycles,151
Index1Cycles,10
Index2Cycles,10

[BCLConvert_Settings]
MinimumTrimmedReadLength,35
MinimumAdapterOverlap,3
MaskShortReads,35
SoftwareVersion,4.2.7

[BCLConvert_Data]
Lane,Sample_ID,index,index2,OverrideCycles,AdapterRead1,AdapterRead2
1,L2301368,GACTGAGTAG,CACTATCAAC,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
1,L2301369,AGTCAGACGA,TGTCGCTGGT,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
1,L2301370,CCGTATGTTC,ACAGTGTATG,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
1,L2301371,GAGTCATAGG,AGCGCCACAC,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
1,L2301372,CTTGCCATTA,CCTTCGTGAT,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
1,L2301373,GAAGCGGCAC,AGTAGAGCCG,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301346_rerun,AGGTCAGATA,TATCTTGTAG,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301347_rerun,CGTCTCATAT,AGCTACTATA,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301348_rerun,ATTCCATAAG,CCACCAGGCA,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301349_rerun,GACGAGATTA,AGGATAATGT,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301350_rerun,AACATCGCGC,ACAAGTGGAC,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301374,TCCATTGCCG,TCGTGCATTC,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301375,CGGTTACGGC,CTATAGTCTT,U7N1Y143;I10;I10;U7N1Y143,CTGTCTCTTATACACATCT,CTGTCTCTTATACACATCT
2,L2301385,GAGCAACA,GCATCTAC,Y151;I8N2;I8N2;Y151,,
2,L2301387,AAGATTGA,GTGGTTCG,Y151;I8N2;I8N2;Y151,,
3,L2301386,CAGTGACG,GAGCGGTA,Y151;I8N2;I8N2;Y151,,
3,L2301388,GTGTGTTT,GAACAATA,Y151;I8N2;I8N2;Y151,,
3,L2301389,TGCGGCGT,TACCGAGG,Y151;I8N2;I8N2;Y151,,
3,L2301390,CATAATAC,CGTTAGAA,Y151;I8N2;I8N2;Y151,,
3,L2301391,GATCTATC,AGCCTCAT,Y151;I8N2;I8N2;Y151,,
3,L2301392,AGCTCGCT,GATTCTGC,Y151;I8N2;I8N2;Y151,,
3,L2301393,CGGAACTG,TCGTAGTG,Y151;I8N2;I8N2;Y151,,
3,L2301395,TTGCCTAG,TAAGTGGT,Y151;I8N2;I8N2;Y151,,
4,L2301321,CCGCGGTT,CTAGCGCT,Y151;I8N2;I8N2;Y151,,
4,L2301322,TTATAACC,TCGATATC,Y151;I8N2;I8N2;Y151,,
4,L2301323,GGACTTGG,CGTCTGCG,Y151;I8N2;I8N2;Y151,,
4,L2301324,AAGTCCAA,TACTCATA,Y151;I8N2;I8N2;Y151,,
4,L2301325,ATCCACTG,ACGCACCT,Y151;I8N2;I8N2;Y151,,
4,L2301326,GCTTGTCA,GTATGTTC,Y151;I8N2;I8N2;Y151,,
4,L2301327,CAAGCTAG,CGCTATGT,Y151;I8N2;I8N2;Y151,,
4,L2301328,TGGATCGA,TATCGCAC,Y151;I8N2;I8N2;Y151,,
4,L2301329,AGTTCAGG,TCTGTTGG,Y151;I8N2;I8N2;Y151,,
4,L2301330,GACCTGAA,CTCACCAA,Y151;I8N2;I8N2;Y151,,
4,L2301331,TCTCTACT,GAACCGCG,Y151;I8N2;I8N2;Y151,,
4,L2301332,CTCTCGTC,AGGTTATA,Y151;I8N2;I8N2;Y151,,
4,L2301333,TAATACAG,GTGAATAT,Y151;I8N2;I8N2;Y151,,
4,L2301334,CGGCGTGA,ACAGGCGC,Y151;I8N2;I8N2;Y151,,
4,L2301335,ATGTAAGT,CATAGAGT,Y151;I8N2;I8N2;Y151,,
4,L2301344,AATCCGGA,AACTGTAG,Y151;I8N2;I8N2;Y151,,
4,L2301389,TGCGGCGT,TACCGAGG,Y151;I8N2;I8N2;Y151,,
4,L2301391,GATCTATC,AGCCTCAT,Y151;I8N2;I8N2;Y151,,
4,L2301394,TAAGGTCA,CTACGACA,Y151;I8N2;I8N2;Y151,,

[Cloud_Settings]
GeneratedVersion,0.0.0
Cloud_Workflow,ica_workflow_1
BCLConvert_Pipeline,urn:ilmn:ica:pipeline:bf93b5cf-cb27-4dfa-846e-acd6eb081aca#BclConvert_v4_2_7

[Cloud_Data]
Sample_ID,LibraryName,LibraryPrepKitName
L2301321,L2301321_CCGCGGTT_CTAGCGCT,TsqSTR
L2301322,L2301322_TTATAACC_TCGATATC,TsqSTR
L2301323,L2301323_GGACTTGG_CGTCTGCG,TsqSTR
L2301324,L2301324_AAGTCCAA_TACTCATA,TsqSTR
L2301325,L2301325_ATCCACTG_ACGCACCT,TsqSTR
L2301326,L2301326_GCTTGTCA_GTATGTTC,TsqSTR
L2301327,L2301327_CAAGCTAG_CGCTATGT,TsqSTR
L2301328,L2301328_TGGATCGA_TATCGCAC,TsqSTR
L2301329,L2301329_AGTTCAGG_TCTGTTGG,TsqSTR
L2301330,L2301330_GACCTGAA_CTCACCAA,TsqSTR
L2301331,L2301331_TCTCTACT_GAACCGCG,TsqSTR
L2301332,L2301332_CTCTCGTC_AGGTTATA,TsqSTR
L2301333,L2301333_TAATACAG_GTGAATAT,TsqSTR
L2301334,L2301334_CGGCGTGA_ACAGGCGC,TsqSTR
L2301335,L2301335_ATGTAAGT_CATAGAGT,TsqSTR
L2301344,L2301344_AATCCGGA_AACTGTAG,TsqSTR
L2301346_rerun,L2301346_rerun_AGGTCAGATA_TATCTTGTAG,ctTSOv2
L2301347_rerun,L2301347_rerun_CGTCTCATAT_AGCTACTATA,ctTSOv2
L2301348_rerun,L2301348_rerun_ATTCCATAAG_CCACCAGGCA,ctTSOv2
L2301349_rerun,L2301349_rerun_GACGAGATTA_AGGATAATGT,ctTSOv2
L2301350_rerun,L2301350_rerun_AACATCGCGC_ACAAGTGGAC,ctTSOv2
L2301368,L2301368_GACTGAGTAG_CACTATCAAC,ctTSOv2
L2301369,L2301369_AGTCAGACGA_TGTCGCTGGT,ctTSOv2
L2301370,L2301370_CCGTATGTTC_ACAGTGTATG,ctTSOv2
L2301371,L2301371_GAGTCATAGG_AGCGCCACAC,ctTSOv2
L2301372,L2301372_CTTGCCATTA_CCTTCGTGAT,ctTSOv2
L2301373,L2301373_GAAGCGGCAC_AGTAGAGCCG,ctTSOv2
L2301374,L2301374_TCCATTGCCG_TCGTGCATTC,ctTSOv2
L2301375,L2301375_CGGTTACGGC_CTATAGTCTT,ctTSOv2
L2301385,L2301385_GAGCAACA_GCATCTAC,NebRNA
L2301386,L2301386_CAGTGACG_GAGCGGTA,NebRNA
L2301387,L2301387_AAGATTGA_GTGGTTCG,NebRNA
L2301388,L2301388_GTGTGTTT_GAACAATA,NebRNA
L2301389,L2301389_TGCGGCGT_TACCGAGG,TsqNano
L2301390,L2301390_CATAATAC_CGTTAGAA,TsqNano
L2301391,L2301391_GATCTATC_AGCCTCAT,TsqNano
L2301392,L2301392_AGCTCGCT_GATTCTGC,TsqNano
L2301393,L2301393_CGGAACTG_TCGTAGTG,TsqNano
L2301394,L2301394_TAAGGTCA_CTACGACA,TsqNano
L2301395,L2301395_TTGCCTAG_TAAGTGGT,TsqNano

[TSO500L_Settings]
AdapterRead1,CTGTCTCTTATACACATCT
AdapterRead2,CTGTCTCTTATACACATCT
AdapterBehaviour,trim
MinimumTrimmedReadLength,35
MaskShortReads,35
OverrideCycles,U7N1Y143;I10;I10;U7N1Y143

[TSO500L_Data]
Sample_ID,Sample_Type,Lane,Index,Index2,I7_Index_ID,I5_Index_ID
L2301346_rerun,DNA,2,AGGTCAGATA,TATCTTGTAG,UDP0002,UDP0002
L2301347_rerun,DNA,2,CGTCTCATAT,AGCTACTATA,UDP0003,UDP0003
L2301348_rerun,DNA,2,ATTCCATAAG,CCACCAGGCA,UDP0004,UDP0004
L2301349_rerun,DNA,2,GACGAGATTA,AGGATAATGT,UDP0005,UDP0005
L2301350_rerun,DNA,2,AACATCGCGC,ACAAGTGGAC,UDP0006,UDP0006
L2301368,DNA,1,GACTGAGTAG,CACTATCAAC,UDP0009,UDP0009
L2301369,DNA,1,AGTCAGACGA,TGTCGCTGGT,UDP0010,UDP0010
L2301370,DNA,1,CCGTATGTTC,ACAGTGTATG,UDP0011,UDP0011
L2301371,DNA,1,GAGTCATAGG,AGCGCCACAC,UDP0012,UDP0012
L2301372,DNA,1,CTTGCCATTA,CCTTCGTGAT,UDP0013,UDP0013
L2301373,DNA,1,GAAGCGGCAC,AGTAGAGCCG,UDP0014,UDP0014
L2301374,DNA,2,TCCATTGCCG,TCGTGCATTC,UDP0015,UDP0015
L2301375,DNA,2,CGGTTACGGC,CTATAGTCTT,UDP0016,UDP0016
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