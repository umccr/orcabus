#!/usr/bin/env python3

"""
SFN LAMBDA PLACEHOLDER: __get_file_from_s3_object_id_lambda_function_arn__
Get file from the s3 object id
"""

import typing
from pathlib import Path
from typing import Dict

from data_sharing_tools import DataTypeEnum
from filemanager_tools import (
    FileObject,
    get_file_object_from_id,
    get_file_object_from_ingest_id
)

if typing.TYPE_CHECKING:
    from data_sharing_tools import FileObjectWithRelativePathTypeDef
    from workflow_tools import WorkflowRun
    from fastq_tools import FastqListRow


def handler(event, context) -> Dict[str, 'FileObjectWithRelativePathTypeDef']:
    """
    Handler function for getting file from the s3 object id
    """

    # Get the s3 object id from the event
    # Check at least one of 's3ObjectId' or 'ingestId' is in the event
    if 's3ObjectId' not in event and 'ingestId' not in event:
        raise ValueError("Either 's3ObjectId' or 'ingestId' must be in the event object")

    # Get the object from either the s3 object id or the ingest id
    if 's3ObjectId' in event:
        # Get the file object from the s3 object id
        file_object: 'FileObject' = get_file_object_from_id(event.get('s3ObjectId'))
    else:
        # Get the file object from the s3 ingest id
        file_object: 'FileObject' = get_file_object_from_ingest_id(event.get('ingestId'))

    # Get the data type
    data_type = DataTypeEnum(event.get("dataType"))

    if data_type == DataTypeEnum.SECONDARY_ANALYSIS:
        # Get workflow from the file object
        workflow_run: 'WorkflowRun' = event.get("workflowRunObject")

        # Get key relative to portal run id
        portal_run_id_part_index = Path(file_object['key']).parts.index(workflow_run['portalRunId'])
        key_relative_to_portal_run_id = "/".join(Path(file_object['key']).parts[portal_run_id_part_index + 1:])

        # Generate the file object with presigned url
        file_object_with_relative_path: 'FileObjectWithRelativePathTypeDef' = dict(
            **file_object,
            **{
                'dataType': data_type.value,
                'relativePath': str(
                    Path('secondary-analysis') /
                    workflow_run['workflow']['workflowName'] /
                    workflow_run['portalRunId'] /
                    key_relative_to_portal_run_id
                )
            }
        )
        return {
            "fileObject": file_object_with_relative_path
        }

    elif data_type == DataTypeEnum.FASTQ:
        fastq_obj: 'FastqListRow' = event.get("fastqObject")
        file_object_with_relative_path: 'FileObjectWithRelativePathTypeDef' = dict(
            **file_object,
            **{
                'dataType': data_type.value,
                'relativePath': str(
                    Path('fastq') /
                    fastq_obj['instrumentRunId'] /
                    f"Lane_{str(fastq_obj['lane'])}" /
                    fastq_obj['library']['libraryId'] /
                    Path(file_object['key']).name
                )
            }
        )
        return {
            "fileObject": file_object_with_relative_path
        }
    else:
        raise ValueError(f"Unsupported data type: {data_type}")


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