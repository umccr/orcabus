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
    from data_sharing_tools.utils.models import WorkflowRunModelSlim


def get_relative_path_for_file_object_for_secondary_analysis(
        file_object: 'FileObject',
        workflow_run_object: 'WorkflowRunModelSlim',
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
        workflow_run_object['workflowName'] /
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
        get_s3_objs_from_ingest_ids_map(event.get('ingestIdList'), currentState="false")
    ))

    # Get the data type
    data_type = DataTypeEnum(event.get("dataType"))

    if data_type == DataTypeEnum.SECONDARY_ANALYSIS:
        # Get workflow from the file object
        workflow_run_object: 'WorkflowRunModelSlim' = event.get("workflowRunObject")

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

#
# if __name__ == "__main__":
#     from os import environ
#     from os import environ
#     import json
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "workflowRunObject": {
#                         "orcabusId": "wv1.01HKGKG700SJ3EW38M7RP8K8BR",
#                         "timestamp": "2024-01-07T00:00:00Z",
#                         "workflowName": "umccrise",
#                         "workflowVersion": "2.3.1--1--9344851",
#                         "portalRunId": "202401075d94d609",
#                         "libraries": [
#                             {
#                                 "libraryId": "L2301517",
#                                 "orcabusId": "lib.01JBMVJ2EPCW8W051H82JF4MTX"
#                             },
#                             {
#                                 "libraryId": "L2301512",
#                                 "orcabusId": "lib.01JBMVJ1DQHB5HA6MP7BDYE94K"
#                             }
#                         ]
#                     },
#                     "dataType": "secondaryAnalysis",
#                     "ingestIdList": [
#                         "01961f56-f1f2-7131-a48c-ae8e75fb9bf0",
#                         "01961f56-f421-7be1-8d0f-77c185f15e82",
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "fileObjectList": [
#     #         {
#     #             "s3ObjectId": "01961f64-4f11-7b72-be97-733c82f47077",
#     #             "eventType": "Created",
#     #             "bucket": "archive-prod-analysis-503977275616-ap-southeast-2",
#     #             "key": "v1/year=2024/month=01/202401075d94d609/L2301517__L2301512/SBJ04470__PRJ231299/structural/SBJ04470__PRJ231299-manta.vcf.gz.tbi",
#     #             "versionId": "jV1Qt72KvQ4WmQ0AqzfDYRVElfv9qWgs",  # pragma: allowlist secret
#     #             "eventTime": "2025-04-10T11:09:49.713633Z",
#     #             "size": 723,
#     #             "sha256": null,
#     #             "lastModifiedDate": "2024-12-11T11:09:58Z",
#     #             "eTag": "\"4be25b00039f42b288f0ae76efbdd756\"",
#     #             "storageClass": "Standard",
#     #             "sequencer": "",
#     #             "isDeleteMarker": false,
#     #             "numberDuplicateEvents": 5,
#     #             "attributes": null,
#     #             "deletedDate": null,
#     #             "deletedSequencer": null,
#     #             "numberReordered": 0,
#     #             "ingestId": "01961f56-f1f2-7131-a48c-ae8e75fb9bf0",
#     #             "isCurrentState": false,
#     #             "reason": "Crawl",
#     #             "archiveStatus": null,
#     #             "isAccessible": false,
#     #             "dataType": "secondaryAnalysis",
#     #             "relativePath": "secondary-analysis/umccrise/202401075d94d609/L2301517__L2301512/SBJ04470__PRJ231299/structural/SBJ04470__PRJ231299-manta.vcf.gz.tbi"
#     #         },
#     #         {
#     #             "s3ObjectId": "01961f64-4f11-7b72-be97-732f83264d06",
#     #             "eventType": "Created",
#     #             "bucket": "archive-prod-analysis-503977275616-ap-southeast-2",
#     #             "key": "v1/year=2024/month=01/202401075d94d609/L2301517__L2301512/SBJ04470__PRJ231299/structural/SBJ04470__PRJ231299-manta.vcf.gz",
#     #             "versionId": "13jUYNWZYmtyYaqAcEAGOXbHJikg_bJX",  # pragma: allowlist secret
#     #             "eventTime": "2025-04-10T11:09:49.713632Z",
#     #             "size": 21817,
#     #             "sha256": null,
#     #             "lastModifiedDate": "2024-12-11T11:09:58Z",
#     #             "eTag": "\"ec8fab0ad7c1061cb9efb778c77d1024\"",
#     #             "storageClass": "Standard",
#     #             "sequencer": "",
#     #             "isDeleteMarker": false,
#     #             "numberDuplicateEvents": 5,
#     #             "attributes": null,
#     #             "deletedDate": null,
#     #             "deletedSequencer": null,
#     #             "numberReordered": 0,
#     #             "ingestId": "01961f56-f421-7be1-8d0f-77c185f15e82",
#     #             "isCurrentState": false,
#     #             "reason": "Crawl",
#     #             "archiveStatus": null,
#     #             "isAccessible": false,
#     #             "dataType": "secondaryAnalysis",
#     #             "relativePath": "secondary-analysis/umccrise/202401075d94d609/L2301517__L2301512/SBJ04470__PRJ231299/structural/SBJ04470__PRJ231299-manta.vcf.gz"
#     #         }
#     #     ]
#     # }
