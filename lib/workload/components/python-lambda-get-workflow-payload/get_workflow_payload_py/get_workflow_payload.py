#!/usr/bin/env python3

"""
Given either a portal run id or a orcabus workflow id, and a workflow status, return the payload of the workflow at that state
"""
from workflow_tools.utils.payload_helpers import get_payload
from workflow_tools.utils.workflow_run_helpers import get_workflow_run_from_portal_run_id, get_workflow_run, \
    get_workflow_run_state


def handler(event, context):
    """
    Takes in either (portal_run_id or orcabus_workflow_id) and workflow_status

    Gets the workflow payload at that state

    Returns the payload object
    :param event:
    :param context:
    :return:
    """

    if event.get("portal_run_id", None) is not None:
        # Get the workflow object from the portal run id
        workflow_obj = get_workflow_run_from_portal_run_id(event.get("portal_run_id"))
    elif event.get("orcabus_workflow_id", None) is not None:
        # Get the workflow object from the orcabus workflow id
        workflow_obj = get_workflow_run(event.get("orcabus_workflow_id"))
    else:
        raise ValueError("Must provide either portal_run_id or orcabus_workflow_id")

    status = event.get("workflow_status", None)

    if status is None:
        raise ValueError("Must provide a workflow_status, i.e 'READY' or 'SUCCEEDED'")

    # Get the READY run state
    workflow_ready_run_state_obj = get_workflow_run_state(workflow_obj.get("orcabusId"), status)
    # Get the payload from the READY run state
    return {
      "payload": get_payload(workflow_ready_run_state_obj.get("payload"))
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['AWS_PROFILE'] = 'umccr-development'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "portal_run_id": "202411071a2c31a3",
#                     "workflow_status": "SUCCEEDED"
#                 },
#                 None
#             ),
#             indent=4
#         ),
#     )
#
#     # {
#     #     "payload": {
#     #         "orcabusId": "pld.01JC28FD1GSVPDKH322NQKTYHR",
#     #         "payloadRefId": "2b5a3f90-4da5-4183-be2d-a88df6c21f1b",
#     #         "version": "2024.07.01",
#     #         "data": {
#     #             "tags": {
#     #                 "libraryId": "L2401547",
#     #                 "sampleType": "WGS",
#     #                 "fastqListRowId": "GACCTGAA.CTCACCAA.3.241024_A00130_0336_BHW7MVDSXC.L2401547",
#     #                 "instrumentRunId": "241024_A00130_0336_BHW7MVDSXC"
#     #             },
#     #             "inputs": {
#     #                 "sampleType": "WGS",
#     #                 "fastqListRow": {
#     #                     "lane": 3,
#     #                     "rgid": "GACCTGAA.CTCACCAA.3.241024_A00130_0336_BHW7MVDSXC.L2401547",
#     #                     "rglb": "L2401547",
#     #                     "rgsm": "L2401547",
#     #                     "read1FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_3/L2401547/L2401547_S16_L003_R1_001.fastq.gz",
#     #                     "read2FileUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/241024_A00130_0336_BHW7MVDSXC/20241030c613872c/Samples/Lane_3/L2401547/L2401547_S16_L003_R2_001.fastq.gz"
#     #                 },
#     #                 "outputPrefix": "L2401547",
#     #                 "fastqListRowId": "GACCTGAA.CTCACCAA.3.241024_A00130_0336_BHW7MVDSXC.L2401547",
#     #                 "dragenReferenceVersion": "v9-r3"
#     #             },
#     #             "outputs": {
#     #                 "multiqcOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgts-qc/202411071a2c31a3/L2401547_dragen_alignment_multiqc/",
#     #                 "multiqcHtmlReportUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgts-qc/202411071a2c31a3/L2401547_dragen_alignment_multiqc/L2401547_dragen_alignment_multiqc.html",
#     #                 "dragenAlignmentBamUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgts-qc/202411071a2c31a3/L2401547_dragen_alignment/L2401547.bam",
#     #                 "dragenAlignmentOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgts-qc/202411071a2c31a3/L2401547_dragen_alignment/"
#     #             },
#     #             "engineParameters": {
#     #                 "logsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/logs/wgts-qc/202411071a2c31a3/",
#     #                 "cacheUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/cache/wgts-qc/202411071a2c31a3/",
#     #                 "outputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/wgts-qc/202411071a2c31a3/",
#     #                 "projectId": "ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
#     #                 "analysisId": "0f2959fa-880a-4fa2-9908-8d12e3c998d5",
#     #                 "pipelineId": "03689516-b7f8-4dca-bba9-8405b85fae45"
#     #             }
#     #         }
#     #     }
#     # }
