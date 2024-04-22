#!/usr/bin/env python3

"""
Launch tes task
"""
import json
from typing import Dict

from libica.openapi.libtes import (
    ApiClient, TaskRunsApi, CreateTaskRunRequest, ApiException, TaskRun
)

import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def get_bs_runs_upload_tes_template_json() -> str:
    return """
    {{
        "name": "orcabus__automated_gds_bs_transfer_{__EXPERIMENT_NAME__}",
        "execution": {{
            "image": {{
                "name": "ghcr.io/umccr/bssh-cli",
                "tag": "1.5.4"
            }},
            "command": "bash",
            "args": [
                "-c",
                "BASESPACE_API_SERVER=\\"${{SECURE_BASESPACE_API_SERVER}}\\" BASESPACE_ACCESS_TOKEN=\\"${{SECURE_BASESPACE_ACCESS_TOKEN}}\\" bs runs upload --verbose --samplesheet {__SAMPLESHEET_NAME__} /mount/mount/media/inputs/{__INPUT_RUN_NAME__} --name {__EXPERIMENT_NAME__} --instrument {__INSTRUMENT__}"
            ],
            "inputs": [
                {{
                    "mode": "stream",
                    "type": "Folder",
                    "url": "{__INPUT_RUN_GDS_PATH__}",
                    "path": "/mount/mount/media/inputs/{__INPUT_RUN_NAME__}"
                }}
            ],
            "outputs": [],
            "systemFiles": {{
                "url": "{__GDS_SYSTEM_FILES_PATH__}"
            }},
            "environment": {{
                "variables": {{
                    "SECURE_BASESPACE_API_SERVER": "{__BASESPACE_API_SERVER__}",
                    "SECURE_BASESPACE_ACCESS_TOKEN": "{__BASESPACE_ACCESS_TOKEN__}"
                }},
                "resources": {{
                    "type": "standardhicpu",
                    "size": "medium"
                }}
            }},
            "retryLimit": 0
        }}
    }}
    """


def populate_bs_runs_upload_template(**kwargs) -> Dict:
    return json.loads(
        get_bs_runs_upload_tes_template_json().format(
            **kwargs,
        )
    )


def launch_tes_task(
    tes_launch_json: Dict
) -> TaskRun:
    """
    Launch TES task
    """
    from .ica_config_helpers import get_ica_tes_configuration

    with ApiClient(get_ica_tes_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = TaskRunsApi(api_client)
    body = CreateTaskRunRequest(
        **tes_launch_json
    )  # CreateTaskRunRequest |  (optional)

    try:
        # Create and launch a task run
        api_response = api_instance.create_task_run(body=body)
    except ApiException as e:
        logger.error("Exception when calling TaskRunsApi->create_task_run: %s\n" % e)
        raise e

    return api_response


