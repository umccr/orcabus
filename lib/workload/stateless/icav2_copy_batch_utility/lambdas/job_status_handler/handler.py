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
    "job_id": "12345"  # FIXME
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

MAX_JOB_ATTEMPT_COUNTER = 5
MAX_JOBS_HANDLED = 10


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    set_icav2_env_vars()

    # Get events
    job_list: List = event.get("job_list")
    job_list_index: int = event.get("job_list_index")

    # Initialise the number of jobs handled
    num_jobs_handled = 0
    job_iterables_to_bump = []  # List of job iterables we can move to the end of the list
    wait = True  # Whether or not to go to wait step or call this function again

    # Loop through the job list starting from the job list index
    for job_iter in range(job_list_index, len(job_list)):
        # Get job object
        job = get_job(job_list[job_iter].get("job_id"))

        # Return status
        if job.status in SUCCESS_STATES:
            job_status = True
        elif job.status in TERMINAL_STATES:
            job_status = False
        elif job.status in RUNNING_STATES:
            job_status = None
        else:
            raise Exception("Unknown job status: {}".format(job.status))

        # Check iterator
        if job_status is False:
            if job_list[job_iter].get("job_attempt_counter", 0) > MAX_JOB_ATTEMPT_COUNTER:
                job_list[job_iter]["job_status"] = False
            # Update the failed jobs list
            job_list[job_iter]["failed_jobs_list"].append(job_list[job_iter].get("job_id"))

            # Get inputs to this job
            dest_uri = job_list[job_iter].get("dest_uri")
            source_uris = job_list[job_iter].get("source_uris")
            job_list[job_iter]["job_id"] = submit_copy_job(
                dest_uri=dest_uri,
                source_uris=source_uris,
            )

            # Set job status to running state
            job_list[job_iter]["job_status"] = None

            # Increment the job attempt counter
            job_list[job_iter]["job_attempt_counter"] += 1

            job_iterables_to_bump.append(job_iter)

        else:
            # Update the job status for the job
            job_list[job_iter]["job_status"] = job_status

        # Increment the number of jobs handled
        num_jobs_handled += 1

        # If the number of jobs handled is greater than the maximum number of jobs handled
        if num_jobs_handled > MAX_JOBS_HANDLED:
            wait = False
            break

    # Move jobs in the job_iterables_to_bump to the end of the list
    # These have just been submitted (again) and we dont want to look at them at the next iteration
    job_list_clean = [job_list[i] for i in range(len(job_list)) if i not in job_iterables_to_bump]
    job_list = job_list_clean + [job_list[i] for i in job_iterables_to_bump]
    del job_list_clean

    # Move all passed and failed copy jobs to the front
    passed_jobs = list(
        filter(
            lambda job_iter_obj: job_iter_obj.get("job_status") is True,
            job_list
        )
    )

    failed_jobs = list(
        filter(
            lambda job_iter_obj: job_iter_obj.get("job_status") is False,
            job_list
        )
    )

    running_jobs = list(
        filter(
            lambda job_iter_obj: job_iter_obj.get("job_status") is None,
            job_list
        )
    )

    # We set the index of the list to the length of the passed jobs
    job_list_index = len(passed_jobs) + len(failed_jobs)

    # Push all running jobs to the back of the list
    job_list = passed_jobs + failed_jobs + running_jobs

    # Return the job list
    return {
        "job_list": job_list,
        "job_list_index": job_list_index,
        "counters": {
            "jobs_failed": len(failed_jobs),
            "jobs_running": len(running_jobs),
            "jobs_passed": len(passed_jobs)
        },
        "wait": wait
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
