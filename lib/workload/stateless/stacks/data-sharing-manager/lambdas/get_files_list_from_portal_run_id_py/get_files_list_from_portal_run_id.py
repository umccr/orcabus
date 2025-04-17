#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __list_files_with_portal_run_id_attribute_lambda_function_arn__

Given a portal run id, this script will return a list of all files associated with that run id.

# FIXME - raise error if the file class is not in available storage

# FIXME - also need to filter out files that should not be shared
# FIXME - but this will take some time to sort. For now, just return all files
"""

import typing
from typing import List, Dict, Any

from filemanager_tools import (
    FileObject,
    list_files_from_portal_run_id
)

if typing.TYPE_CHECKING:
    from data_sharing_tools.utils.models import WorkflowRunModelSlim

import re

REGEX_FILES_BY_WORKFLOW_NAME = {
    "umccrise": [
        # Top level reports
        re.compile(r"multiqc_report\.html$"),
        re.compile(r"somatic\.pcgr\.html$"),
        re.compile(r"normal\.cpsr\.html$"),
        re.compile(r"cancer_report\.html$"),
        # Small variants
        re.compile(r"germline\.predispose_genes\.vcf\.gz$"),
        re.compile(r"germline\.predispose_genes\.vcf\.gz\.tbi$"),
        re.compile(r"somatic-PASS\.vcf\.gz$"),
        re.compile(r"somatic-PASS\.vcf\.gz\.tbi$"),
        re.compile(r"somatic\.pcgr\.snvs_indels\.tiers\.tsv$"),
        # Structural variants
        re.compile(r"manta\.tsv$"),
        re.compile(r"manta\.vcf\.gz$"),
        re.compile(r"manta\.vcf\.gz.tbi$"),
        # Purple files
        re.compile(r"purple\.cnv\.gene\.tsv$"),
        re.compile(r"purple\.cnv\.somatic\.tsv$"),
        # Amber files
        re.compile(r"\.amber\.baf\.pcf"),
        re.compile(r"\.amber\.baf\.tsv"),
        re.compile(r"\.amber\.baf\.vcf\.gz"),
        re.compile(r"\.amber\.baf\.vcf\.gz\.tbi"),
        re.compile(r"\.amber\.contamination\.tsv"),
        re.compile(r"\.amber\.contamination\.vcf\.gz"),
        re.compile(r"\.amber\.contamination\.vcf\.gz\.tbi"),
        re.compile(r"\.amber\.qc"),
        re.compile(r"amber.version"),
        # Cobalt files
        re.compile(r"\.cobalt\.gc\.median\.tsv"),
        re.compile(r"\.cobalt\.ratio\.median\.tsv"),
        re.compile(r"\.cobalt\.ratio\.pcf"),
        re.compile(r"\.chr\.len"),
        re.compile(r"\.cobalt\.gc\.median\.tsv"),
        re.compile(r"\.cobalt\.ratio\.pcf"),
        re.compile(r"\.cobalt\.ratio\.tsv"),
        re.compile(r"cobalt\.version"),
        # Signature
        re.compile(r"-indel\.tsv\.gz"),
        re.compile(r"-snv_2015\.tsv\.gz"),
        re.compile(r"-snv_2020\.tsv\.gz"),
    ],
    "tumor-normal": [
        re.compile(r"tumor\.bam$"),
        re.compile(r"tumor\.bam\.bai$"),
        re.compile(r"tumor\.bam\.md5sum$"),
        re.compile(r"normal\.bam$"),
        re.compile(r"normal\.bam\.bai$"),
        re.compile(r"normal\.bam\.md5sum$"),
    ],
    "wts": [
        re.compile(r".bam$"),
        re.compile(r".bam.bai$"),
        re.compile(r".bam.md5sum$"),
        re.compile(r"fusion_candidates.final$"),
        re.compile(r"quant.genes.sf$"),
        re.compile(r"quant.sf")
    ]
}


def handler(event: Dict, context: Any) -> Dict[str, List[str]]:
    """
    Given a portal run id, this script will return a list of all files associated with that run id.
    :param event:
    :param context:
    :return:
    """

    # Get the portal run id from the event
    workflow_object: 'WorkflowRunModelSlim' = event['workflowRunObject']

    # Get the portal run id from the workflow object
    portal_run_id = workflow_object['portalRunId']

    file_obj_list = list_files_from_portal_run_id(
        portal_run_id=portal_run_id,
        workflow_name=workflow_object['workflowName'],
        currentState="false"
    )

    # Filter files by workflow type
    if workflow_object['workflowName'] in REGEX_FILES_BY_WORKFLOW_NAME:
        file_object_list_filtered = []
        for file_object_iter_ in file_obj_list:
            for regex_iter_ in REGEX_FILES_BY_WORKFLOW_NAME[workflow_object['workflowName']]:
                if regex_iter_.search(file_object_iter_['key']):
                    file_object_list_filtered.append(file_object_iter_)
                    break
    else:
        file_object_list_filtered = file_obj_list

    # Sort by relative paths
    relative_paths = list(set(list(map(
        lambda file_obj_iter_: re.match(f'.*/{portal_run_id}/(.*)', file_obj_iter_['key']).group(1),
        file_object_list_filtered
    ))))

    # If we have more than one file in the relative path
    file_object_list_filtered_with_no_deleted_marker = []
    for rel_path in relative_paths:
        files_matching_rel_path = sorted(
            list(filter(
                lambda file_object_iter_: re.match(f'.*/{portal_run_id}/{rel_path}$', file_object_iter_['key']),
                file_object_list_filtered
            )),
            key=lambda file_object_iter_: file_object_iter_['eventTime'], reverse=True
        )
        # Now we need to group by the full uri path, we may have multiple copies of this file
        # Filter out any copies that are marked as deleted
        key_list = list(set(list(map(
            lambda file_object_iter_: file_object_iter_['key'],
            files_matching_rel_path
        ))))

        for key_iter_ in key_list:
            try:
                _ = list(map(
                    lambda file_object_iter_: file_object_iter_['eventType'],
                    list(filter(
                        lambda file_object_iter_: file_object_iter_['key'] == key_iter_,
                        files_matching_rel_path
                    ))
                )).index("Deleted")
            except ValueError:
                # This file has not been deleted
                # Take the object with an ingest id
                file_object_list_filtered_with_no_deleted_marker.append(
                    next(filter(
                        lambda file_object_iter_: (
                                file_object_iter_['key'] == key_iter_ and
                                file_object_iter_['ingestId'] is not None
                        ),
                        files_matching_rel_path
                    ))
                )
            else:
                # This file has been deleted
                continue

    return {
        "ingestIdList": list(set(list(map(
            lambda file_object_iter_: file_object_iter_['ingestId'],
            file_object_list_filtered_with_no_deleted_marker
        ))))
    }


# if __name__ == "__main__":
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
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "ingestIdList": [
#     #         "01932e37-01a1-7d12-9a69-006d44292b5b",
#     #         "01932e37-0290-76e0-8d03-b624c925c4ae",
#     #         ....
#     #         "01932e41-26a2-7b31-9487-c6e679d80cd1"
#     #     ]
#     # }
#

# if __name__ == "__main__":
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
#                         "orcabusId": "wv1.01HKGKG70074SSADGKHRFRAA9M",
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
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "ingestIdList": [
#     #         "01932e37-01a1-7d12-9a69-006d44292b5b",
#     #         "01932e37-0290-76e0-8d03-b624c925c4ae",
#     #         ....
#     #         "01932e41-26a2-7b31-9487-c6e679d80cd1"
#     #     ]
#     # }
# #


# if __name__ == "__main__":
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
#                         "orcabusId": "wfr.01JD20PQGM58RYT7WMK9KQK0XE",
#                         "timestamp": "2024-09-15T11:02:38.140000Z",
#                         "portalRunId": "202409157b57b94a",  # pragma: allowlist secret
#                         "workflowName": "umccrise",
#                         "workflowVersion": "2.3.1",
#                         "libraries": [
#                             {
#                                 "orcabusId": "lib.01JBMVZRC90TM1R4WF6WM75KD4",
#                                 "libraryId": "L2401365"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBMVZRB85AY759W9CX9JRJMD",
#                                 "libraryId": "L2401364"
#                             }
#                         ]
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "ingestIdList": [
#     #         "01932e37-01a1-7d12-9a69-006d44292b5b",
#     #         "01932e37-0290-76e0-8d03-b624c925c4ae",
#     #         ....
#     #         "01932e41-26a2-7b31-9487-c6e679d80cd1"
#     #     ]
#     # }
# #


# if __name__ == "__main__":
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
#                         "orcabusId": "wv1.01HZB3XW00SD59RB456ZFBM1M6",
#                         "timestamp": "2024-06-02T00:00:00Z",
#                         "workflowName": "umccrise",
#                         "workflowVersion": "2.3.1--1--9344851",
#                         "portalRunId": "20240602e4238704",
#                         "libraries": [
#                             {
#                                 "libraryId": "L2400668",
#                                 "orcabusId": "lib.01JBMVY7RK8ZDRZEKMPV8K60Z3"
#                             },
#                             {
#                                 "libraryId": "L2400667",
#                                 "orcabusId": "lib.01JBMVY7QFA11HR5J4JS3Y2Y6K"
#                             }
#                         ]
#                     }
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "ingestIdList": [
#     #         "01932e37-01a1-7d12-9a69-006d44292b5b",
#     #         "01932e37-0290-76e0-8d03-b624c925c4ae",
#     #         ....
#     #         "01932e41-26a2-7b31-9487-c6e679d80cd1"
#     #     ]
#     # }
# #
