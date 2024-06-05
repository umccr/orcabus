#!/usr/bin/env python3

"""
Launch bs runs upload command via TES


Takes in the following SequenceRunManager event

{
  "gds_folder_path": "/Runs/240315_A01052_0186_AH5HM5DSXC_r.YpC_0U_7-06Oom1cFl9Y5A",
  "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
  "samplesheet_name": "SampleSheet.csv",
}

With the following environment variables
ICA_BASE_URL
ICA_ACCESS_TOKEN_SECRET_ID
PORTAL_TOKEN_SECRET_ID
SS_CHECK_API_DOMAIN_PARAMETER_NAME

And performs the following operations:

1. Collects the SampleSheet.csv from the gds folder path
2. Runs the samplesheet csv against the sscheck backend lambda to collect an ICAv2 SampleSheet object
3. Uploads the ICAv2 SampleSheet object back to the GDS location -> this should be renamed from SampleSheet.csv to SampleSheet.V2.<timestamp>.csv

The lambda should fail on the following conditions

1. If the SampleSheet.csv is not found in the gdsFolderPath
2. If the SampleSheet.csv cannot be converted to a v2 samplesheet via the sscheck backend lambda
3. If the ICAv2 SampleSheet cannot be uploaded back to the gdsFolderPath

Returns the following object:

{
  "samplesheet_name": "SampleSheet.V2.timestamp.csv"
}
"""
from pathlib import Path

from bs_runs_upload_manager_tools.utils.gds_helpers import upload_file_to_gds, download_file_from_gds
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

from bs_runs_upload_manager_tools.utils.ica_config_helpers import set_ica_env_vars
from bs_runs_upload_manager_tools.utils.portal_helpers import set_portal_token, set_api_url
from bs_runs_upload_manager_tools.utils.samplesheet_helpers import generate_v2_samplesheet


def download_samplesheet_to_temp_dir(samplesheet_path: str) -> Path:
    """
    Downloads the samplesheet from the gds path to a temporary directory
    """
    named_temp_file_obj = NamedTemporaryFile(suffix=".csv", delete=False)
    local_samplesheet_path = Path(named_temp_file_obj.name)

    download_file_from_gds(
        gds_path=samplesheet_path,
        local_path=local_samplesheet_path
    )

    return local_samplesheet_path


def handler(event, context):
    # Set environment variables ICA_BASE_URL and ICA_ACCESS_TOKEN
    set_ica_env_vars()
    set_portal_token()
    set_api_url()

    # Get the event parameters
    gds_folder_path = event["gds_folder_path"]
    gds_volume_name = event["gds_volume_name"]
    samplesheet_name = event["samplesheet_name"]

    # Download samplesheet
    samplesheet_file = download_samplesheet_to_temp_dir(
        samplesheet_path=f"gds://{gds_volume_name}{gds_folder_path}/{samplesheet_name}",
    )

    # Collect v2 from ss backend lambda
    v2_samplesheet = generate_v2_samplesheet(
        v1_samplesheet_file=samplesheet_file,
    )

    # Get current time
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))

    samplesheet_name = f"SampleSheet.V2.{timestamp}.csv"

    # Upload v2 samplesheet
    upload_file_to_gds(
        local_path=v2_samplesheet,
        gds_path=f"gds://{gds_volume_name}{gds_folder_path}/{samplesheet_name}",
    )

    return {
        "samplesheet_name": samplesheet_name,
        "samplesheet_gds_path": f"gds://{gds_volume_name}{gds_folder_path}/{samplesheet_name}"
    }


# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "gds_folder_path": "/Runs/231109_A01052_0171_BHLJW7DSX7_r.NULhvzxcSEWmqZw8QljXfQ",
#                     "samplesheet_name": "SampleSheet.csv",
#                     "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
