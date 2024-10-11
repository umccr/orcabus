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

If the job is complete, check the reports for the case to see if the report generation is also complete

Also return the DynamoDB object to the expression reference and the object dict since
the object can vary depending on what status the job / report is at

job_status:  STR VALUE OF THE JOB STATUS
job_status_bool:  BOOL VALUE OF THE JOB STATUS  TRUE IF COMPLETE, FALSE IF FAILED, NONE OTHERWISE
report_id:  INT VALUE OF THE REPORT ID
report_status: STR VALUE OF THE REPORT STATUS
report_status_bool: BOOL VALUE OF THE REPORT STATUS  TRUE IF COMPLETE, FALSE IF FAILED, NONE OTHERWISE
job_status_changed: BOOL VALUE OF WHETHER THE JOB STATUS HAS CHANGED TRUE OR FALSE
expression_attribute_values_dict: DICT OF THE EXPRESSION ATTRIBUTE VALUES FOR DYNAMODB UPDATE EXPRESSION
update_expression_str: STR OF THE UPDATE EXPRESSION FOR DYNAMODB

"""

# Standard imports
import logging
from os import environ

# Layer imports
from pieriandx_pipeline_tools.utils.pieriandx_helpers import get_pieriandx_client
from pieriandx_pipeline_tools.utils.secretsmanager_helpers import set_pieriandx_env_vars

# Set logger
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


REPORT_STATUS_BOOL = {
    "waiting": None,
    "ready": None,
    "running": None,
    "report_generation_complete": True,
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
    case_id = event.get("case_id", None)
    job_id = event.get("informaticsjob_id", None)
    report_id = event.get("report_id", None)
    current_job_status = event.get("current_job_status", None)
    current_report_status = event.get("current_report_status", None)

    # Initialise job status
    job_status = None

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

    if report_id is None or report_id == -1:
        # Get the informatics job object
        try:
            informaticsjob_obj = next(
                filter(
                    lambda informaticsjob_iter: int(informaticsjob_iter.get("id")) == int(job_id),
                    case_data.get("informaticsJobs")
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

        # Job has either failed or is incomplete - return as is
        if (
                (
                    # Job not yet complete
                    not JOB_STATUS_BOOL[job_status]
                ) or
                (
                    # Reports empty
                    case_data.get("reports") is None
                ) or
                (
                    # Reports length is empty
                    len(case_data.get("reports")) == 0
                )
        ):
            # Set the expression attribute values dict
            expression_attribute_values_dict = {
                ":job_status": {
                    "S": job_status
                }
            }
            update_expression_str = "SET job_status = :job_status"

            if JOB_STATUS_BOOL[job_status] is not None:
                expression_attribute_values_dict[":job_status_bool"] = {
                    "BOOL": JOB_STATUS_BOOL[job_status]
                }
                update_expression_str = f"{update_expression_str}, job_status_bool = :job_status_bool"

            if JOB_STATUS_BOOL[job_status] is False:
                expression_attribute_values_dict[":workflow_status"] = {
                    "S": "FAILED"
                }
                update_expression_str = f"{update_expression_str}, workflow_status = :workflow_status"

            # Return the job status
            return {
                "job_status": job_status,
                "job_status_bool": JOB_STATUS_BOOL[job_status],
                "report_id": None,
                "report_status": None,
                "report_status_bool": None,
                "job_status_changed": False if job_status == current_job_status else True,
                "expression_attribute_values_dict": expression_attribute_values_dict,
                "update_expression_str": update_expression_str
            }

        # Job is complete and reports not empty, check reports
        reportjob_obj = case_data.get("reports")[0]

    else:
        # Report id is not None, get the report object
        try:
            reportjob_obj =  next(
                filter(
                    lambda reportjob_iter: int(reportjob_iter.get("id")) == int(report_id),
                    case_data.get("reports")
                )
            )
        except StopIteration:
            logger.error(f"Failed to get report id {report_id}")
            return {
                "status": "failed",
                "message": f"Failed to get report id {report_id} from the case id {case_id}"
            }

    # Reinitialise job status
    job_status = "complete" if job_status is None else job_status

    # Get report  status
    report_status = reportjob_obj.get("status")

    # Return the job status with the report status
    # expression_attribute_values_dict
    # update_expression_str

    # Set the expression attribute values dict
    expression_attribute_values_dict = {
        ":job_status": {
            "S": job_status
        },
        ":report_id": {
            "S": reportjob_obj.get("id")
        },
        ":report_status": {
            "S": report_status
        },
    }
    update_expression_str = "SET job_status = :job_status, report_id = :report_id, report_status = :report_status"

    # Add the bool values if they are not None
    if JOB_STATUS_BOOL[job_status] is not None:
        expression_attribute_values_dict[":job_status_bool"] = {
            "BOOL": JOB_STATUS_BOOL[job_status]
        }
        update_expression_str = f"{update_expression_str}, job_status_bool = :job_status_bool"

    if REPORT_STATUS_BOOL[report_status] is not None:
        expression_attribute_values_dict[":report_status_bool"] = {
            "BOOL": REPORT_STATUS_BOOL[report_status]
        }
        update_expression_str = f"{update_expression_str}, report_status_bool = :report_status_bool"

    # Add the workflow status
    # If one of the job status or report status are false, then the workflow status is failed
    if JOB_STATUS_BOOL[job_status] is False or REPORT_STATUS_BOOL[report_status] is False:
        expression_attribute_values_dict[":workflow_status"] = {
            "S": "FAILED"
        }
        update_expression_str = f"{update_expression_str}, workflow_status = :workflow_status"
    # If both the job status and report status are true, then the workflow status is complete
    elif JOB_STATUS_BOOL[job_status] is True and REPORT_STATUS_BOOL[report_status] is True:
        expression_attribute_values_dict[":workflow_status"] = {
            "S": "COMPLETE"
        }
        update_expression_str = f"{update_expression_str}, workflow_status = :workflow_status"

    return {
        "job_status": job_status,
        "job_status_bool": JOB_STATUS_BOOL[job_status],
        "report_id": reportjob_obj.get("id"),
        "report_status": report_status,
        "report_status_bool": REPORT_STATUS_BOOL[report_status],
        "job_status_changed": False if report_status == current_report_status else True,
        "expression_attribute_values_dict": expression_attribute_values_dict,
        "update_expression_str": update_expression_str
    }



# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PIERIANDX_BASE_URL'] = "https://app.uat.pieriandx.com/cgw-api/v2.0.0"
#     environ['PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME'] = "collectPierianDxAccessToken"
#     environ['PIERIANDX_INSTITUTION'] = "melbournetest"
#     environ['PIERIANDX_USER_EMAIL'] = "services@umccr.org"
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "current_report_status": "",
#                     "informaticsjob_id": 45813,
#                     "report_id": -1,
#                     "case_id": 103511,
#                     "current_job_status": "waiting"
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
# # {
# #   "job_status": "complete",
# #   "job_status_bool": true,
# #   "report_id": "37981",
# #   "report_status": "complete",
# #   "report_status_bool": true,
# #   "job_status_changed": false,
# #   "expression_attribute_values_dict": {
# #     ":job_status": {
# #       "S": "complete"
# #     },
# #     ":report_status": {
# #       "S": "complete"
# #     },
# #     ":job_status_bool": {
# #       "BOOL": true
# #     },
# #     ":report_status_bool": {
# #       "BOOL": true
# #     },
# #     ":workflow_status": {
# #       "S": "COMPLETE"
# #     }
# #   },
# #   "update_expression_str": "SET job_status = :job_status, report_status = :report_status, job_status_bool = :job_status_bool, report_status_bool = :report_status_bool, workflow_status = :workflow_status"
# # }
