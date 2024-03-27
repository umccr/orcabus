#!/usr/bin/env python3

"""
Launch bs runs upload command via TES

Takes in the following SequenceRunManager event

{
  "gds_folder_path": "/Runs/240315_A01052_0186_AH5HM5DSXC_r.YpC_0U_7-06Oom1cFl9Y5A",
  "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
  "samplesheet_name": "SampleSheet.V2.timestamp.csv",
  "instrument_run_id": "240315_A01052_0186_AH5HM5DSXC",
}

With the following environment variables
* BASESPACE_API_SERVER
* BASESPACE_ACCESS_TOKEN_SECRET_ID
* ICA_BASE_URL
* ICA_ACCESS_TOKEN_SECRET_ID
* GDS_SYSTEM_FILES_PATH


And performs the following operations

1. Collects the secret for bs auth
2. Populates the TES RUNS Template API
3. Launches the bs runs upload command to upload the ICAv2 SampleSheet object to the BaseSpace run

{
  "task_run_id": "trn.12345"
}
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict
from urllib.parse import urlparse

from bs_runs_upload_manager_tools.utils.aws_secrets_manager_helpers import get_secret_string
from bs_runs_upload_manager_tools.utils.ica_config_helpers import set_ica_env_vars
from bs_runs_upload_manager_tools.utils.tes_helpers import launch_tes_task, populate_bs_runs_upload_template


def handler(event, context):
    """
    Given a gds_folder_path, gds_volume_name and the samplesheet_name, launch the bs runs upload command via TES

    Args:
        event:
        context:

    Returns:

    """
    # Set environment variables ICA_BASE_URL and ICA_ACCESS_TOKEN
    set_ica_env_vars()

    # Ensure environment variables are set
    for env_var in [
        "BASESPACE_API_SERVER",
        "BASESPACE_ACCESS_TOKEN_SECRET_ID",
        "ICA_BASE_URL",
        "ICA_ACCESS_TOKEN_SECRET_ID",
        "GDS_SYSTEM_FILES_PATH"
    ]:
        assert (
            os.environ.get(env_var),
            f"{env_var} environment variable is not set"
        )

    for event_key in [
        "gds_folder_path",
        "gds_volume_name",
        "samplesheet_name",
        "instrument_run_id"
    ]:
        assert (
            event.get(event_key, None) is not None,
            f"{event_key} key is not set in the event"
        )

    # Populate the TES task run json
    task_run_json: Dict = populate_bs_runs_upload_template(
        __BASESPACE_API_SERVER__=os.environ.get("BASESPACE_API_SERVER"),
        __BASESPACE_ACCESS_TOKEN__=get_secret_string(
            os.environ.get("BASESPACE_ACCESS_TOKEN_SECRET_ID")
        ),
        __INPUT_RUN_NAME__=Path(event.get("gds_folder_path")).name,
        __EXPERIMENT_NAME__=event.get("instrument_run_id"),
        __INSTRUMENT__=os.environ.get("INSTRUMENT", "NovaSeq6000"),
        __INPUT_RUN_GDS_PATH__="gds://" + event.get("gds_volume_name") + event.get("gds_folder_path"),
        __SAMPLESHEET_NAME__=event.get("samplesheet_name"),
        __GDS_SYSTEM_FILES_PATH__=(
                "gds://" +
                urlparse(os.environ.get("GDS_SYSTEM_FILES_PATH")).netloc +
                str(
                    Path(urlparse(os.environ.get("GDS_SYSTEM_FILES_PATH")).path) /
                    event.get("instrument_run_id") /
                    str(int(datetime.now(timezone.utc).timestamp()))
                )
        )
    )

    return (
        {
            "task_run_id": launch_tes_task(task_run_json).id
        }
    )


if __name__ == "__main__":
    import json
    print(
        json.dumps(
            handler(
                {
                    "gds_folder_path": "/Runs/231109_A01052_0171_BHLJW7DSX7_r.NULhvzxcSEWmqZw8QljXfQ",
                    "samplesheet_name": "SampleSheet.V2.1711336300.924772.csv",
                    "gds_volume_name": "bssh.acddbfda498038ed99fa94fe79523959",
                    "instrument_run_id": "231109_A01052_0171_BHLJW7DSX7"
                },
                None
            ),
            indent=2
        )
    )
