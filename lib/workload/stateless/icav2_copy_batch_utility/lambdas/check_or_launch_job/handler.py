#!/usr/bin/env python3

"""
Lambda to determine if a given ICAv2 Copy Job has finished.
Returns the status of the job which is one of the following
* INITIALIZED
* WAITING_FOR_RESOURCES
* RUNNING
* STOPPED
* SUCCEEDED
* PARTIALLY_SUCCEEDED
* FAILED

The event input is
{
    "dest_uri": "icav2://path/to/destination/folder/"
    "source_uris": [
        "icav2://path/to/data",
        "icav2://path/to/data2",
    ]
    "job_id": null  # Or the job id abcd-1234-efgh-5678
    "failed_job_list": []  # Empty list or list of failed jobs
    "job_status": One of RUNNING, SUCCEEDED or FAILED (not the same as the job states, we reu)
    "wait_time_seconds": int  # Number of seconds to wait before checking the job status - we double this each time we go through this loop
}

"""
from pathlib import Path
from typing import List

# Wrapica imports
from wrapica.job import get_job

# Local imports
from icav2_copy_batch_utility_tools.utils.job_helpers import submit_copy_job
from icav2_copy_batch_utility_tools.utils.aws_ssm_helpers import set_icav2_env_vars

# Globals
SUCCESS_STATES = [
    "SUCCEEDED"
]
TERMINAL_STATES = [
    "STOPPED",
    "FAILED",
    "PARTIALLY_SUCCEEDED"
]
RUNNING_STATES = [
    "INITIALIZED",
    "WAITING_FOR_RESOURCES",
    "RUNNING"
]


# Try a job 10 times before giving up
MAX_JOB_ATTEMPT_COUNTER = 10
DEFAULT_WAIT_TIME_SECONDS = 10


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get events
    dest_uri = event.get("dest_uri")
    source_uris = event.get("source_uris")
    job_id = event.get("job_id")
    failed_job_list = event.get("failed_job_list")
    job_status = event.get("job_status")
    wait_time_seconds = event.get("wait_time_seconds")

    # Check if job is None
    if job_id is None:
        # First time through
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_uri=dest_uri,
                source_uris=source_uris,
            ),
            "failed_job_list": [],  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }

    # Else job id is not none
    job_obj = get_job(job_id)

    # Check job status

    # Return status
    if job_obj.status in SUCCESS_STATES:
        job_status = True
    elif job_obj.status in TERMINAL_STATES:
        job_status = False
    elif job_obj.status in RUNNING_STATES:
        job_status = None
    else:
        raise Exception("Unknown job status: {}".format(job_obj.status))

    # Check if we're still running
    if job_status is None:
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": job_id,
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": wait_time_seconds * 2  # Wait a bit longer
        }

    # Handle a failed job
    if job_status is False:
        # Add this job id to the failed job list
        failed_job_list.append(job_id)

        # Check we haven't exceeded the excess number of attempts
        if len(failed_job_list) >= MAX_JOB_ATTEMPT_COUNTER:
            # Most important bit is that the job_status is set to failed
            return {
                "dest_uri": dest_uri,
                "source_uris": source_uris,
                "job_id": None,
                "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
                "job_status": "FAILED",
                "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
            }

        # Return a new job with new wait time
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": submit_copy_job(
                dest_uri=dest_uri,
                source_uris=source_uris,
            ),
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "RUNNING",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }

    # Handle successful job
    if job_status is True:
        return {
            "dest_uri": dest_uri,
            "source_uris": source_uris,
            "job_id": job_id,
            "failed_job_list": failed_job_list,  # Empty list or list of failed jobs
            "job_status": "SUCCEEDED",
            "wait_time_seconds": DEFAULT_WAIT_TIME_SECONDS
        }

# if __name__ == "__main__":
#     import json
#
#     print(
#         json.dumps(
#             handler(
#                 event={
#                     "job_list": [
#                         {
#                             "job_attempt_counter": 1,
#                             "job_id": "d80ea8f4-b2a4-4b5f-840f-2426584d0495",
#                             "failed_jobs_list": [],
#                             "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/InterOp/",
#                             "source_uris": [
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/AlignmentMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EmpiricalPhasingMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/CorrectedIntMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/BasecallingMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ErrorMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtendedTileMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/OpticalModelMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsByLaneOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtractionMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/PFGridMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ImageMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/TileMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetrics2030Out.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/FWHMGridMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EventMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/RegistrationMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/IndexMetricsOut.bin"
#                             ],
#                             "job_status": True
#                         },
#                         {
#                             "job_attempt_counter": 1,
#                             "job_id": "7c240086-6c62-4328-96f1-66b7c6430fc4",
#                             "failed_jobs_list": [],
#                             "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/Reports/",
#                             "source_uris": [
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Adapter_Metrics.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Demultiplex_Stats.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Quality_Metrics.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Index_Hopping_Counts.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Adapter_Cycle_Metrics.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/SampleSheet.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/RunInfo.xml",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/fastq_list.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/IndexMetricsOut.bin",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Top_Unknown_Barcodes.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Demultiplex_Tile_Stats.csv",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/report.html",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Quality_Tile_Metrics.csv"
#                             ],
#                             "job_status": True
#                         },
#                         {
#                             "job_attempt_counter": 1,
#                             "job_id": "f768bacc-3639-4417-a55a-937ef64c02e7",
#                             "failed_jobs_list": [],
#                             "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/Samples/Lane_1/L2301368/",
#                             "source_uris": [
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301368/L2301368_S1_L001_R1_001.fastq.gz",
#                                 "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301368/L2301368_S1_L001_R2_001.fastq.gz"
#                             ],
#                             "job_status": True
#                         },
#                         ...
#                     ],
#                     "job_list_index": 8,
#                     "counters": {
#                         "jobs_failed": 0,
#                         "jobs_running": 42,
#                         "jobs_passed": 8
#                     },
#                     "wait": False
#                 }
#                 ,
#                 context=None
#             )
#         )
#     )
#
#     # {
#     #   "job_list": [
#     #     {
#     #       "job_attempt_counter": 1,
#     #       "job_id": "d80ea8f4-b2a4-4b5f-840f-2426584d0495",
#     #       "failed_jobs_list": [],
#     #       "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/InterOp/",
#     #       "source_uris": [
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/AlignmentMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EmpiricalPhasingMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/CorrectedIntMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/BasecallingMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ErrorMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtendedTileMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/OpticalModelMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsByLaneOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ExtractionMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/PFGridMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/ImageMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/TileMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetrics2030Out.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/FWHMGridMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/QMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/EventMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/RegistrationMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-runs/bssh_aps2-sh-prod_3661659/InterOp/IndexMetricsOut.bin"
#     #       ],
#     #       "job_status": true
#     #     },
#     #     {
#     #       "job_attempt_counter": 1,
#     #       "job_id": "7c240086-6c62-4328-96f1-66b7c6430fc4",
#     #       "failed_jobs_list": [],
#     #       "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/Reports/",
#     #       "source_uris": [
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Adapter_Metrics.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Demultiplex_Stats.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Quality_Metrics.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Index_Hopping_Counts.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Adapter_Cycle_Metrics.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/SampleSheet.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/RunInfo.xml",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/fastq_list.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/IndexMetricsOut.bin",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Top_Unknown_Barcodes.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Demultiplex_Tile_Stats.csv",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/report.html",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Reports/Quality_Tile_Metrics.csv"
#     #       ],
#     #       "job_status": true
#     #     },
#     #     {
#     #       "job_attempt_counter": 1,
#     #       "job_id": "f768bacc-3639-4417-a55a-937ef64c02e7",
#     #       "failed_jobs_list": [],
#     #       "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/Samples/Lane_1/L2301368/",
#     #       "source_uris": [
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301368/L2301368_S1_L001_R1_001.fastq.gz",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301368/L2301368_S1_L001_R2_001.fastq.gz"
#     #       ],
#     #       "job_status": true
#     #     },
#     #     {
#     #       "job_attempt_counter": 1,
#     #       "job_id": "b99b7780-718a-4f30-9441-57244d5f228f",
#     #       "failed_jobs_list": [],
#     #       "dest_uri": "icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/ilmn_primary/2023/231116_A01052_0172_BHVLM5DSX7/3661659/20240307135959/Samples/Lane_1/L2301369/",
#     #       "source_uris": [
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301369/L2301369_S2_L001_R1_001.fastq.gz",
#     #         "icav2://b23fb516-d852-4985-adcc-831c12e8cd22/ilmn-analyses/231116_A01052_0172_BHVLM5DSX7_d24651_4c90dc-BclConvert v4_2_7-b719c8d9-5e6d-49e6-a8be-ca17b5e9d40b/output/Samples/Lane_1/L2301369/L2301369_S2_L001_R2_001.fastq.gz"
#     #       ],
#     #       "job_status": true
#     #     },
#     #     ...
#     #   ],
#     #   "job_list_index": 18,
#     #   "counters": {
#     #     "jobs_failed": 0,
#     #     "jobs_running": 32,
#     #     "jobs_passed": 18
#     #   },
#     #   "wait": false
#     # }
