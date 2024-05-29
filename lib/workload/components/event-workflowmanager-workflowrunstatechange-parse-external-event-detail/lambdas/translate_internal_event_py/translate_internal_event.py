#!/usr/bin/env python3

"""
Given an event, update the source and eventbus name,
Given the uuid update the data.payload.refId attribute with the uuid


"""
import json
import logging
from os import environ
from datetime import datetime, timezone

from workflowrunstatechange import WorkflowRunStateChange, AWSEvent, Marshaller

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    # Get values
    event_detail_input = event.get('event_detail_input', None)
    ref_uuid = event.get('uuid', None)

    # Confirm event_input is set
    if event_detail_input is None:
        raise ValueError('Event detail input is not set')

    # Confirm ref_uuid is set
    if ref_uuid is None:
        raise ValueError('UUID is not set')

    event_detail_output = WorkflowRunStateChange(
        portal_run_id=event_detail_input['portalRunId'],
        timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z"),
        status=event_detail_input['status'],
        workflow_name=event_detail_input['workflowName'],
        workflow_version=event_detail_input['workflowVersion'],
        workflow_run_name=event_detail_input['workflowRunName'],
        payload=event_detail_input['payload']
    )

    # Update reference id
    event_detail_output.payload['refId'] = ref_uuid

    # Update event payload with new data
    return {
        "event_detail_output": Marshaller.marshall(event_detail_output),
    }


# if __name__ == '__main__':
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "event_detail_input": {
#                         "portalRunId": '20xxxxxxxxxx',
#                         "timestamp": "2024-00-25T00:07:00Z",
#                         "status": "SUCCEEDED",
#                         "workflowName": "BclConvert",
#                         "workflowVersion": "4.2.7",
#                         "workflowRunName": "123456_A1234_0000_TestingPattern",
#                         "payload": {
#                             "refId": None,
#                             "version": "0.1.0",
#                             "data": {
#                                 "projectId": "valid_project_id",
#                                 "analysisId": "valid_payload_id",
#                                 "userReference": "123456_A1234_0000_TestingPattern",
#                                 "timeCreated": "2024-01-01T00:11:35Z",
#                                 "timeModified": "2024-01-01T01:24:29Z",
#                                 "pipelineId": "valid_pipeline_id",
#                                 "pipelineCode": "BclConvert v0_0_0",
#                                 "pipelineDescription": "BclConvert pipeline.",
#                                 "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
#                             }
#                         },
#                         "detail-type": "WorkflowRunStateChange"
#                     },
#                     "uuid": '018fa7ec-281c-7b78-b055-0524cc636ead'
#                 },
#                 None
#             ),
#             indent=2
#         )
#     )
#
#     # {
#     #   "event_detail_output": {
#     #     "portalRunId": "20xxxxxxxxxx",
#     #     "timestamp": "2024-05-29T09:23:37Z",
#     #     "status": "SUCCEEDED",
#     #     "workflowName": "BclConvert",
#     #     "workflowVersion": "4.2.7",
#     #     "workflowRunName": "123456_A1234_0000_TestingPattern",
#     #     "payload": {
#     #       "refId": "018fa7ec-281c-7b78-b055-0524cc636ead",
#     #       "version": "0.1.0",
#     #       "data": {
#     #         "projectId": "valid_project_id",
#     #         "analysisId": "valid_payload_id",
#     #         "userReference": "123456_A1234_0000_TestingPattern",
#     #         "timeCreated": "2024-01-01T00:11:35Z",
#     #         "timeModified": "2024-01-01T01:24:29Z",
#     #         "pipelineId": "valid_pipeline_id",
#     #         "pipelineCode": "BclConvert v0_0_0",
#     #         "pipelineDescription": "BclConvert pipeline.",
#     #         "pipelineUrn": "urn:ilmn:ica:pipeline:123456-abcd-efghi-1234-acdefg1234a#BclConvert_v0_0_0"
#     #       }
#     #     }
#     #   }
#     # }
