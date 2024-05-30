data_json="$(
  jq --null-input --raw-output \
    '
      {
        "instrumentRunId": "240229_A00130_0288_BH5HM2DSXC",
        "fastqListRowsB64gz": "H4sIAAxnWGYC/9WbW2vcSBCF/4qZ51gj9UWXvHU6bCfgvES9EFgWodjjxZCExAmBZNn/vlWaSceJzrSZeaoG21NIxj7UR1XXabX++nfzOrx8vnl6sQnOxehDrGJ0MTgKms2TC7o9vuLbV8rUdVOr/bWrZ79fu5o/7Ohaw7d3803zx9273Z/3d/xrd9fzV/V0u+3sYHf9rbrU6kZfmuuuvZy1MpfX7dzbm3nXd2/t9uP93fv5/tt0M3+Zt/T3lRomR/9F11Ot+n569sK+eKWej2/8VtV03+pave2b7tbutuP8/uO73ecta5ma7Q95KZjGZrqiaHrdTPRR3c6fv3yq/vm+OYhWskWrX0X/9+TiIT3mF0JkfsHTlw8OEbTDmuD+mliCdkjBNKpCCELROYIEMATvnPeV9y7SV3QBEWzrNcH9NbEE2zoF06gLIQhF5wg+wPYAJiLYAIKNbII/g2k0pRBEovNdNDI3bp2BaQbqo7gGwTrYyl4HW5WCabSlEESis110WQOD85FqkD4WnJCgBgS1bII6BdPYlkIQic4RpOmTq85HXgcjtVCGCAkaQNDIJmhSMI1dKQSR6CzBSNyoezrPXoLoHZ1kWkCwlU2wTcE09qUQRKIf6aL7xunZFFINVmpNb7BrevtrB3pKDL0fq8hgUzCNAydCyaWXFZ2lx22TRhnqn9RI2RIieqD2hlY2vTYFZIrrUvBB1dkpNBI1F5buGRcPgfh1gF8nm1+XAspEUwo/qDq7/vlAC14M7OPp06P6U3rtAQ/XpPIjeSmgTKgy+B1Rna0/Lj7iRh7QcSV6yK8H/HrZ/PoUUCZ0Kfyg6sc8IJv3itY+6p4R198A+A2y+Q0poEyYUvhB1dn646mTflS09tH0Atc/+l7zM7VofqZOAWXCFsIPqz7NPegz3IMWw08fHcS1XHxZ0ae5B32GexBIbz2Hl4APqj7NPegz3INAfus5vAR+UPVp7kGf4R7E8UNzuHx+R1Sf5h70Ge5BIL/1HF4CP6j6NPegz3APAvmt5/AS+EHVp7kHfYZ7kMcPzOEF8MOq8/Nn4KrjwfMAkAaZyoCnR8BBtA8dhBHDMD1BsymgbCxPQ41chnnVj9TgfunjJ7mOA8BvAKdghkY0v6FJAWWiK4QfVn2ahzBneAiB/NbTeAn8oOrsSbTIx2DIw3MRcgz59YBfL5tfnwLKRF8KP6g6X3+R3V9kD7Gcywb8lAEe0IjunyQvBZSJoQx+R1TnZ5il6nyVtkIRPwX4Kdn80qawmkZVl8IPqs6fxY78LoRbTqB53gxF/IAHNINsfkMKKBNNKfyg6vw5Xq5AT/0z+uUwIeJngQe0tWh+tk4BZUIVwg+rzvsH7w97oIudh/VnwfpnZa9/tkkBZUKXwg+qzu5hLyevPT9DWnazA+QH1j8re/2zKgWUCVMKP6g66x/4RRZiR/MLvxHhHeSnAT8tm59OAWXClsIPqs77P7bv0VVsJJZnuIifAfyMbH4/A8pEWwo/qPqR95CocVLbdFx8BBDys4Cflc3PpoAy0ZXCD6rO+gd+a8Xz/LI8Sjqy/rWAXyubX5sCykRfCj+oOr//EpZnD1VcBlHs/2wH+HWy+XUpoEyUsv+CVf/O7+//AU/7iMPMQAAA",
	      "outputUri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/240229_A00130_0288_BH5HM2DSXC/202405302b817f5e/"
      }
    ' \
)"

payload_json="$(
  jq --null-input --raw-output \
    --argjson data_json "${data_json}" \
    '
      {
        "refId": null,
        "version": "2024.05.15",
        "data": $data_json
      }
    ' \
)"

portal_run_id="$(date +"%Y%m%d")$(xxd -l 4 -c 4 -p < /dev/random)"
utc_time="$(date --utc --iso-8601=seconds | sed 's/+00:00/Z/')"
detail_json="$(
  jq --null-input --raw-output \
    --argjson payload_json "${payload_json}" \
    --arg utc_time "${utc_time}" \
    --arg portal_run_id "${portal_run_id}" \
    '
      {
        "status": "succeeded",
	"timestamp": $utc_time,
        "workflowName": "bsshFastqCopy",
        "workflowVersion": "1.0.0",
	"workflowRunName": "umccr__orcabus__automated__240229_A00130_0288_BH5HM2DSXC__\($portal_run_id)",
        "portalRunId": $portal_run_id,
        "payload":  $payload_json
      }
    ' \
)"

event_entry="$(
  jq --null-input --raw-output --compact-output \
    --arg utc_time "${utc_time}" \
    --argjson input_detail "${detail_json}" \
    '
      {
        "Entries": [
          {
            "EventBusName": "OrcaBusMain",
            "DetailType": "WorkflowRunStateChange",
            "Source": "orcabus.bsshfastqcopymanager",
            "Time": $utc_time,
            "Resources": [],
            "Detail": ( $input_detail | tojson )
          }
        ]
      }
    ' \
)"

aws events put-events --cli-input-json "${event_entry}"
