#!/usr/bin/env python3

"""
Use the boto3 api to list a service's instances
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
    service_id = event["service_id"]

    service_discovery_client = get_service_discovery_client()

    service_instances = list(
        map(
            lambda service_instance_iter_: {
              "instance_id": service_instance_iter_['Id'],
              "instance_attributes": list(
                  map(
                    lambda instance_kv_iter_: {
                        "attr_key": instance_kv_iter_[0],
                        "attr_value": instance_kv_iter_[1],
                    },
                    service_instance_iter_['Attributes'].items()
                  )
              ),
            },
            service_discovery_client.list_instances(ServiceId=service_id)['Instances']
        )
    )

    return {
        "service_instances": service_instances
    }


# if __name__ == "__main__":
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "service_id": "srv-zuvfka3fyqxswwme"
#                 },
#                 None
#             ),
#             indent=4
#         )
#
#     )
#
#     # {
#     #     "service_instances": [
#     #         {
#     #             "instance_id": "HolmesLocalDevTestStackServiceNonIpD37CD7BB",
#     #             "instance_attributes": [
#     #                 {
#     #                     "attr_key": "checkLambdaArn",
#     #                     "attr_value": "arn:aws:lambda:ap-southeast-2:843407916570:function:HolmesLocalDevTestStack-CheckFunction82225D96-gtKl1C5USxIO"
#     #                 },
#     #                 {
#     #                     "attr_key": "controlLambdaArn",
#     #                     "attr_value": "arn:aws:lambda:ap-southeast-2:843407916570:function:HolmesLocalDevTestStack-ControlFunction8A0764F3-zunc6vUJbVGz"
#     #                 },
#     #                 {
#     #                     "attr_key": "extractStepsArn",
#     #                     "attr_value": "arn:aws:states:ap-southeast-2:843407916570:stateMachine:SomalierExtractStateMachine59E102CC-CEqwe36xUrru"
#     #                 },
#     #                 {
#     #                     "attr_key": "listLambdaArn",
#     #                     "attr_value": "arn:aws:lambda:ap-southeast-2:843407916570:function:HolmesLocalDevTestStack-ListFunction89E6AFAD-WXt699CK8CMD"
#     #                 },
#     #                 {
#     #                     "attr_key": "relateLambdaArn",
#     #                     "attr_value": "arn:aws:lambda:ap-southeast-2:843407916570:function:HolmesLocalDevTestStack-RelateFunction666B2CBC-2KKtCnoqHQ5F"
#     #                 }
#     #             ]
#     #         }
#     #     ]
#     # }
