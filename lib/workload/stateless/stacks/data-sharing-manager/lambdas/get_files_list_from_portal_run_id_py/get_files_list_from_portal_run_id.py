#!/usr/bin/env python3

"""
SFN LAMBDA FUNCTION PLACEHOLDER: __list_files_with_portal_run_id_attribute_lambda_function_arn__

Given a portal run id, this script will return a list of all files associated with that run id.

# FIXME - raise error if the file class is not in available storage

# FIXME - also need to filter out files that should not be shared
# FIXME - but this will take some time to sort. For now, just return all files
"""

import typing
from typing import List, Dict

from filemanager_tools import (
    FileObject,
    list_files_from_portal_run_id
)

if typing.TYPE_CHECKING:
    from workflow_tools import WorkflowRun


def handler(event, context) -> Dict[str, List['FileObject']]:
    """
    Given a portal run id, this script will return a list of all files associated with that run id.
    :param event:
    :param context:
    :return:
    """

    # Get the portal run id from the event
    workflow_object: 'WorkflowRun' = event['workflowRunObject']

    # Get the portal run id from the workflow object
    portal_run_id = workflow_object['portalRunId']

    # Get the list of files associated with the portal run id
    file_obj_list = list_files_from_portal_run_id(portal_run_id)

    return {
        "ingestIdList": list(filter(
            lambda file_ingest_id_iter_: file_ingest_id_iter_ is not None,
            list(map(
                lambda file_object_iter_: file_object_iter_['ingestId'],
                file_obj_list
            ))
        ))
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
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "workflowRunObject": {
#                         "orcabusId": "wfr.01JBDS3QR4PNY7S2NKPBBR529W",
#                         "currentState": {
#                             "orcabusId": "stt.01JBDVMWKQHD7MP0HQHKGY0ARE",
#                             "status": "RESOLVED",
#                             "timestamp": "2024-10-30T04:41:17.130000Z"
#                         },
#                         "libraries": [
#                             {
#                                 "orcabusId": "lib.01J9T9CM4RZMBSACRK7R4DPJZD",
#                                 "libraryId": "L2401499"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y205V55QZPFBHCGGMJH6",
#                                 "libraryId": "L2401526"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y22Q2CPCZR69JS6EK8QP",
#                                 "libraryId": "L2401527"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y26QQ4GBSVK48W1XWD6T",
#                                 "libraryId": "L2401528"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2APRAEVKTXHC14BV5QV",
#                                 "libraryId": "L2401529"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2EHZZ850EN28EWKH55H",
#                                 "libraryId": "L2401530"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2H072091A41CKQTNC5C",
#                                 "libraryId": "L2401531"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2KCNZD76XSP2SZZCRPJ",
#                                 "libraryId": "L2401532"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2QJA4ECHFMNRY1DESHP",
#                                 "libraryId": "L2401533"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y2WRMS894XNSDJEWNSQD",
#                                 "libraryId": "L2401534"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y31GBQHP4X90PZ28X14R",
#                                 "libraryId": "L2401535"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y33XXNSGDDHX48413FMK",
#                                 "libraryId": "L2401536"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y36HJ7TJZJ3Q4BXD7J07",
#                                 "libraryId": "L2401537"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3901PA0X3FBMWBKYNMB",
#                                 "libraryId": "L2401538"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3BE906M3CXFBQGV2FKE",
#                                 "libraryId": "L2401539"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3DZ55KF4D5KVMJP7DSN",
#                                 "libraryId": "L2401540"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3GAN479FC5MJG19HPJM",
#                                 "libraryId": "L2401541"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3JN6A228K20Y5XC549F",
#                                 "libraryId": "L2401542"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3N1VHKBRSKEV4B3KZXN",
#                                 "libraryId": "L2401543"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3QGZSGF74W6CTV0JJ16",
#                                 "libraryId": "L2401544"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3TF8CPCSGC6KGCW3RBM",
#                                 "libraryId": "L2401545"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y3YMTRWYNT4F6DAS3YP7",
#                                 "libraryId": "L2401546"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y411MZ9J2JSGX332MD3T",
#                                 "libraryId": "L2401547"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y44ZSWKBXJJFHRHJ94CK",
#                                 "libraryId": "L2401548"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y47CCZW8RTC4YF8NDSAP",
#                                 "libraryId": "L2401549"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y4HG0MFWTHSXQQSHR90F",
#                                 "libraryId": "L2401552"
#                             },
#                             {
#                                 "orcabusId": "lib.01JBB5Y4NNR06DNJQ7R9JGPFY9",
#                                 "libraryId": "L2401553"
#                             }
#                         ],
#                         "workflow": {
#                             "orcabusId": "wfl.01JBDS3QP7CXFZBG4AR0FXMCF0",
#                             "workflowName": "bsshFastqCopy",
#                             "workflowVersion": "2024.05.24",
#                             "executionEngine": "Unknown",
#                             "executionEnginePipelineId": "Unknown"
#                         },
#                         "analysisRun": None,
#                         "portalRunId": "20241030c613872c",  #  pragma: allowlist secret
#                         "executionId": None,
#                         "workflowRunName": "umccr--automated--bsshfastqcopy--2024-05-24--20241030c613872c",
#                         "comment": None
#                     }
#                 }
#                 ,
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
