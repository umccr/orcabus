from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_lambda_destinations as lambda_destinations
)
from constructs import Construct


class ICAV1Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, orcabus_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        props = self.node.try_get_context("props")

        icav1_queue = sqs.Queue(
            self,
            f"{construct_id}ICAV1Queue",
            visibility_timeout=Duration.seconds(300),
            queue_name=f"{props['namespace']}-icav1-ens"
        )

        icav1_queue.grant_send_messages(iam.AccountPrincipal('079623148045'))  # ICA AWS account

        ################################################################################
        # Lambda for event sourcing
        # Lambda purpose: record all event, de-duplicate event, send de-duplicate event to the bus

        self.event_source_lambda = lambda_.Function(
            self,
            f"{construct_id}EventSourceLambda",
            code=lambda_.Code.from_asset("lambdas/functions/icav1/event_source"),
            handler="event_source.handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            description="Lambda to event source before sending to the orcabus",
            function_name=f"{construct_id}-event-source-icav1",
            memory_size=1769,
            timeout=Duration.seconds(30),
            on_success=lambda_destinations.EventBridgeDestination(event_bus=orcabus_stack.event_bus),
            environment={
                "STORE_EVENT_BUCKET_NAME": orcabus_stack.s3_store_event
            }
        )

        orcabus_stack.event_bus.grant_put_events_to(self.event_source_lambda)

    #     ################################################################################
    #     # Lambda
    #
    #     # Lambda layers for shared libs
    #     util_lambda_layer = self.create_lambda_layer(scope=self, name="eb_util")
    #     schema_lambda_layer = self.create_lambda_layer(scope=self, name="schemas")
    #
    #     # lambda environment variables
    #     lambda_env = {
    #         "EVENT_BUS_NAME": props['namespace']
    #     }
    #
    #     # Lambda to manage workflow events
    #     orchestrator_lambda = self.create_standard_lambda(scope=self, name="orchestrator",
    #                                                       layers=[util_lambda_layer, schema_lambda_layer],
    #                                                       env=lambda_env)
    #     orcabus_stack.grant_put_events_to(orchestrator_lambda)
    #
    #     # Lambda to prepare BCL Convert workflows
    #     bcl_convert_lambda = self.create_standard_lambda(scope=self, name="bcl_convert",
    #                                                      layers=[util_lambda_layer, schema_lambda_layer],
    #                                                      env=lambda_env)
    #     event_bus.grant_put_events_to(bcl_convert_lambda)
    #
    #     # Lambda to prepare WGS QC workflows
    #     dragen_wgs_qc_lambda = self.create_standard_lambda(scope=self, name="dragen_wgs_qc",
    #                                                        layers=[util_lambda_layer, schema_lambda_layer],
    #                                                        env=lambda_env)
    #     event_bus.grant_put_events_to(dragen_wgs_qc_lambda)
    #
    #     # Lambda to prepare WGS somatic analysis workflows
    #     dragen_wgs_somatic_lambda = self.create_standard_lambda(scope=self, name="dragen_wgs_somatic",
    #                                                             layers=[util_lambda_layer, schema_lambda_layer],
    #                                                             env=lambda_env)
    #     event_bus.grant_put_events_to(dragen_wgs_somatic_lambda)
    #
    #     # Lambda to submit WES workflows to ICA
    #     wes_launcher_lambda = self.create_standard_lambda(scope=self, name="wes_launcher",
    #                                                       layers=[util_lambda_layer, schema_lambda_layer])
    #     event_bus.grant_put_events_to(wes_launcher_lambda)
    #
    #     # Lambda to handle GDS events (translating outside events into application events + dedup/persisting)
    #     gds_manager_lambda = self.create_standard_lambda(scope=self, name="gds_manager", layers=[util_lambda_layer])
    #     event_bus.grant_put_events_to(gds_manager_lambda)
    #
    #     # Lamda to handle ENS events (translating outside events into application events + dedup/persisting)
    #     ens_manager_lambda = self.create_standard_lambda(scope=self, name="ens_event_manager",
    #                                                      layers=[util_lambda_layer, schema_lambda_layer],
    #                                                      env=lambda_env)
    #     event_bus.grant_put_events_to(ens_manager_lambda)
    #     ens_manager_lambda.grant_invoke(wes_launcher_lambda)
    #
    #     ################################################################################
    #     # Event Rules setup
    #
    #     # route ENS events to the orchestrator
    #     self.create_event_rule(name="WorkflowRun", bus=event_bus, handler=orchestrator_lambda,
    #                            event_type=EventType.WRSC, event_source=EventSource.ENS_HANDLER)
    #
    #     self.create_event_rule(name="SequenceRun", bus=event_bus, handler=orchestrator_lambda,
    #                            event_type=EventType.SRSC, event_source=EventSource.ENS_HANDLER)
    #
    #     # route orchestrator events on to their next steps
    #     self.create_event_rule(name="BclConvert", bus=event_bus, handler=bcl_convert_lambda,
    #                            event_type=EventType.SRSC, event_source=EventSource.ORCHESTRATOR)
    #
    #     self.create_event_rule(name="DragenWgsQc", bus=event_bus, handler=dragen_wgs_qc_lambda,
    #                            event_type=EventType.DRAGEN_WGS_QC, event_source=EventSource.ORCHESTRATOR)
    #
    #     self.create_event_rule(name="DragenWgsSomatic", bus=event_bus, handler=dragen_wgs_somatic_lambda,
    #                            event_type=EventType.DRAGEN_WGS_SOMATIC, event_source=EventSource.ORCHESTRATOR)
    #
    #     # route WES launch events to the WES launcher
    #     self.create_event_rule(name="BclConvertLaunch", bus=event_bus, handler=wes_launcher_lambda,
    #                            event_type=EventType.WES_LAUNCH, event_source=EventSource.BCL_CONVERT)
    #
    #     self.create_event_rule(name="DragenWgsQcLaunchRequest", bus=event_bus, handler=wes_launcher_lambda,
    #                            event_type=EventType.WES_LAUNCH, event_source=EventSource.DRAGEN_WGS_QC)
    #
    #     self.create_event_rule(name="DragenWgsSomaticLaunch", bus=event_bus, handler=wes_launcher_lambda,
    #                            event_type=EventType.WES_LAUNCH, event_source=EventSource.DRAGEN_WGS_SOMATIC)
    #
    # # TODO: refactor to allow separate function path/name (allow better code organisation)
    # def create_standard_lambda(self, scope, name: str, layers: list = [], env: dict = {}, duration_seconds: int = 20):
    #     id = camel_case_upper(f"{self.namespace}_{name}_Lambda")
    #     function_name = f"{self.namespace}_{name}"
    #     # TODO: switch to aws_cdk.aws_lambda_python -> PythonFunction
    #     return lmbda.Function(scope=scope,
    #                           id=id,
    #                           function_name=function_name,
    #                           handler=f"{name}.handler",
    #                           runtime=lmbda.Runtime.PYTHON_3_8,
    #                           code=lmbda.Code.from_asset(f"lambdas/functions/{name}"),
    #                           environment=env,
    #                           timeout=Duration.seconds(duration_seconds),
    #                           layers=layers)
    #
    # def create_lambda_layer(self, scope, name: str) -> lmbda.LayerVersion:
    #     # NOTE: currently requires manual packaging
    #     # TODO: switch to aws_cdk.aws_lambda_python -> PythonLayerVersion
    #     id = camel_case_upper(f"{self.namespace}_{name}_Layer")
    #     return lmbda.LayerVersion(
    #         scope=scope,
    #         id=id,
    #         code=lmbda.Code.from_asset(f"lambdas/layers/{name}.zip"),
    #         compatible_runtimes=[lmbda.Runtime.PYTHON_3_8],
    #         description=f"Lambda layer {name} for python 3.8"
    #     )
    #
    # def create_event_rule(self, name, bus: events.EventBus, handler: lmbda.Function, event_type: EventType,
    #                       event_source: EventSource):
    #     wgs_somatic_to_wes_launcher_rule = events.Rule(
    #         scope=self,
    #         id=f"{name}Rule",
    #         rule_name=f"{name}Rule",
    #         description=f"Rule to send {event_type.value} events to the {handler.function_name} Lambda",
    #         event_bus=bus)
    #     wgs_somatic_to_wes_launcher_rule.add_target(target=targets.LambdaFunction(handler=handler))
    #     wgs_somatic_to_wes_launcher_rule.add_event_pattern(detail_type=[event_type.value],
    #                                                        source=[event_source.value])
