#!/usr/bin/env python3

"""
Use the boto3 api to discover the services running in the AWS account.

SERVICE NAME is 'fingerprint'
"""

import typing
import boto3
from os import environ

if typing.TYPE_CHECKING:
    from mypy_boto3_servicediscovery import ServiceDiscoveryClient


def get_service_discovery_client() -> 'ServiceDiscoveryClient':
    return boto3.client('servicediscovery')


def handler(event, context):
    """

    :return:
    """
    service_name = event['service_name']

    service_discovery_client = get_service_discovery_client()

    service_object = next(
        filter(
            lambda service_iter_: service_iter_['Name'] == service_name,
            service_discovery_client.list_services()['Services']
        )
    )

    return {
        "service_obj": {
            "service_id": service_object['Id'],
            "service_name": service_object['Name'],
            "service_arn": service_object['Arn'],
        }
    }


# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "service_name": 'fingerprint'
#                 },
#                 None
#             ),
#             indent=4
#         )
#
#     )
#
#     # {
#     #     "service_obj": {
#     #         "service_id": "srv-zuvfka3fyqxswwme",
#     #         "service_name": "fingerprint",
#     #         "service_arn": "arn:aws:servicediscovery:ap-southeast-2:843407916570:service/srv-zuvfka3fyqxswwme"
#     #     }
#     # }
