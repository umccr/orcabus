#!/usr/bin/env python3

"""
SFN LAMBDA PLACEHOLDER: __get_file_from_s3_object_id_lambda_function_arn__
Get file from the s3 object id
"""

import typing
from pathlib import Path
from typing import Dict, List

from data_sharing_tools import DataTypeEnum
from filemanager_tools import (
    FileObject,
    get_s3_objs_from_ingest_ids_map
)

if typing.TYPE_CHECKING:
    from data_sharing_tools import FileObjectWithRelativePathTypeDef
    from workflow_tools import WorkflowRun


def get_relative_path_for_file_object_for_secondary_analysis(
    file_object: 'FileObject',
    workflow_run_object: 'WorkflowRun',
):
    """
    Get the relative path for the file object
    """

    # Get key relative to portal run id
    portal_run_id_part_index = Path(file_object['key']).parts.index(workflow_run_object['portalRunId'])
    key_relative_to_portal_run_id = "/".join(Path(file_object['key']).parts[portal_run_id_part_index + 1:])

    # Generate the file object with presigned url
    return str(
        Path('secondary-analysis') /
        workflow_run_object['workflow']['workflowName'] /
        workflow_run_object['portalRunId'] /
        key_relative_to_portal_run_id
    )

def handler(event, context) -> Dict[str, List['FileObjectWithRelativePathTypeDef']]:
    """
    Handler function for getting file from the s3 object id
    """

    # Get the s3 object id from the event
    # Check at least one of 's3ObjectId' or 'ingestId' is in the event
    file_object_list: List['FileObject'] = list(map(
        lambda ingest_file_iter_: ingest_file_iter_.get('fileObject'),
        get_s3_objs_from_ingest_ids_map(event.get('ingestIdList'))
    ))

    # Get the data type
    data_type = DataTypeEnum(event.get("dataType"))

    if data_type == DataTypeEnum.SECONDARY_ANALYSIS:
        # Get workflow from the file object
        workflow_run_object: 'WorkflowRun' = event.get("workflowRunObject")

        # Get key relative to portal run id
        return {
            "fileObjectList": list(map(
                lambda file_object_iter_: dict(
                    **file_object_iter_,
                    **{
                        'dataType': data_type.value,
                        'relativePath': get_relative_path_for_file_object_for_secondary_analysis(
                            file_object_iter_,
                            workflow_run_object
                        )
                    }
                ),
                file_object_list
            ))
        }
    raise NotImplementedError("Lambda function only supports secondary analysis data type")

# if __name__ == "__main__":
#     from os import environ
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "ingestId": "01932e37-0168-71c2-a167-5def1d2474cb",
#                     "workflowRunObject": {
#                         "orcabusId": "wfr.01JCPJQ3YA7Y539QEN95ZRD8DE",
#                         "currentState": {
#                             "orcabusId": "stt.01JCQ49EBDG742K6TSPHXVYF8N",
#                             "status": "SUCCEEDED",
#                             "timestamp": "2024-11-15T05:21:10.289000Z"
#                         },
#                         "libraries": [
#                             {
#                                 "orcabusId": "lib.01JBB5Y411MZ9J2JSGX332MD3T",
#                                 "libraryId": "L2401547"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3YMTRWYNT4F6DAS3YP7",
#                                 "libraryId": "L2401546"
#                             }
#                         ],
#                         "workflow": {
#                             "orcabusId": "wfl.01JBGCW3Z9ERKSX5E61JQYSYAJ",
#                             "workflowName": "tumor-normal",
#                             "workflowVersion": "4.2.4",
#                             "executionEngine": "Unknown",
#                             "executionEnginePipelineId": "Unknown"
#                         },
#                         "analysisRun": None,
#                         "portalRunId": "2024111463c05a04",
#                         "executionId": None,
#                         "workflowRunName": "umccr--automated--tumor-normal--4-2-4--2024111463c05a04",
#                         "comment": None,
#                     },
#                     "dataType": "secondaryAnalysis"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "fileObject": {
#     #         "s3ObjectId": "01932e36-ffc5-7fe0-b526-7bd50ce3a643",
#     #         "eventType": "Created",
#     #         "bucket": "pipeline-dev-cache-503977275616-ap-southeast-2",
#     #         "key": "byob-icav2/development/analysis/tumor-normal/2024111463c05a04/L2401546_dragen_germline/L2401546.hard-filtered.vcf.gz.tbi",
#     #         "versionId": "null",
#     #         "eventTime": "2024-11-15T05:06:10Z",
#     #         "size": 1689719,
#     #         "sha256": null,
#     #         "lastModifiedDate": "2024-11-15T05:06:11Z",
#     #         "eTag": "\"c1deaf85050662d00010514a4a6719d0\"",
#     #         "storageClass": "Standard",
#     #         "sequencer": "006736D6C205EF7E0F",  # pragma: allowlist secret
#     #         "isDeleteMarker": false,
#     #         "numberDuplicateEvents": 0,
#     #         "attributes": {
#     #             "portalRunId": "2024111463c05a04"
#     #         },
#     #         "deletedDate": null,
#     #         "deletedSequencer": null,
#     #         "numberReordered": 0,
#     #         "ingestId": "01932e37-0168-71c2-a167-5def1d2474cb",
#     #         "isCurrentState": true,
#     #         "reason": "Unknown",
#     #         "archiveStatus": null,
#     #         "isAccessible": true,
#     #         "dataType": "secondaryAnalysis",
#     #         "relativePath": "secondary-analysis/tumor-normal/2024111463c05a04/L2401546_dragen_germline/L2401546.hard-filtered.vcf.gz.tbi"
#     #     }
#     # }