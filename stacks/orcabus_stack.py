from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_events as events,
    aws_s3 as s3,
)

from re import sub


def camel_case_upper(string: str):
    string = sub(r"([_\-])+", " ", string).title().replace(" ", "")
    return string


class OrcabusStack(Stack):
    namespace = None

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        props = self.node.try_get_context("props")

        ################################################################################
        # Event Bus

        self.event_bus = events.EventBus(scope=self,
                                         id=f"{construct_id}EventBus",
                                         event_bus_name=props['namespace'])

        ################################################################################
        # S3 to source event
        self.s3_store_event = s3.Bucket(
            auto_delete_objects=True,  # TODO: Change false when production
            removal_policy=RemovalPolicy.DESTROY,  # TODO: change to RemovalPolicy.RETAIN on production
            bucket_name="ica-event-source-store",
        )
