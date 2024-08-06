#!/usr/bin/env python3

"""
Get informatics job status

Given a case id and an informatics job id, return the status of the job

The job status can be one of the following:
* waiting  #  PROCESSING
* ready    #  PROCESSING
* running  #  PROCESSING
* complete #  TERMINAL
* failed   #  TERMINAL
* canceled #  TERMINAL
"""

import logging
from os import environ

from pieriandx_pipeline_tools.utils.pieriandx_helpers import get_pieriandx_client
from requests import Response

from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_pieriandx_env_vars


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


JOB_STATUS_BOOL = {
    "waiting": None,
    "ready": None,
    "running": None,
    "complete": True,
    "failed": False,
    "canceled": False
}


def handler(event, context):
    """
    Get informatics job status
    Args:
        event:
        context:

    Returns:

    """

    # Get event values
    case_id = event.get("case_id")
    job_id = event.get("informaticsjob_id")


    # Cannot query the job id directly, instead query the case id and get the job id from there
    set_pieriandx_env_vars()

    # Set pyriandx client
    pyriandx_client = get_pieriandx_client(
        email=environ['PIERIANDX_USER_EMAIL'],
        token=environ['PIERIANDX_USER_AUTH_TOKEN'],
        instiution=environ['PIERIANDX_INSTITUTION'],
        base_url=environ['PIERIANDX_BASE_URL'],
    )

    case_data = pyriandx_client._get_api(
        endpoint=f"/case/{case_id}",
    )

    # Get the informatics job id
    informaticsjobs = case_data.get("informaticsJobs")

    # Get the informatics job object
    try:
        informaticsjob_obj = next(
            filter(
                lambda informaticsjob_iter: int(informaticsjob_iter.get("id")) == int(job_id),
                informaticsjobs
            )
        )
    except StopIteration:
        logger.error(f"Failed to get informatics job {job_id}")
        return {
            "status": "failed",
            "message": f"Failed to get informatics job {job_id} from the case id {case_id}"
        }

    # Get job status
    job_status = informaticsjob_obj.get("status")

    # Return the job status
    return {
        "status": job_status,
        "status_bool": JOB_STATUS_BOOL[job_status]
    }

#
# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "case_id": "101031",
#                     "informaticsjob_id": "43366"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
