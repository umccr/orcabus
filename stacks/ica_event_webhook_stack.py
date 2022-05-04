from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_events as events,
    # aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as lmbda,
    aws_apigateway as apigw,
)


class WebhookStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props.get("namespace", "default")  # namespace in camelcase

        bus = events.EventBus.from_event_bus_name(
            self, id="OrcaBus", event_bus_name="OrcaBus"
        )

        lambda_role = iam.Role(
            scope=self,
            id="Role",
            role_name="stripeAppRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonEventBridgeFullAccess"
                ),
            ],
        )

        wh_lambda_name = "wh_lambda"
        wh_lambda = lmbda.Function(
            scope=self,
            id="icaWebhookEventHandler",
            function_name=wh_lambda_name,
            handler=f"{wh_lambda_name}.handler",
            runtime=lmbda.Runtime.PYTHON_3_9,
            code=lmbda.Code.from_asset(f"lambdas/functions/{wh_lambda_name}"),
            timeout=Duration.seconds(10),
            role=lambda_role,
        )
        bus.grant_put_events_to(wh_lambda)

        wh_api_gw = apigw.LambdaRestApi(self, "icaWebhookAPI", handler=wh_lambda)
        CfnOutput(self, "ApiGatewayUrlForPath", value=wh_api_gw.url_for_path())
        CfnOutput(self, "ApiGatewayUrl", value=wh_api_gw.url)

        # event = events.Rule(self, 'stripeWebhookEventRule',
        #                     rule_name='stripeWebhookEventRule',
        #                     enabled=True,
        #                     event_bus=bus,
        #                     description='all success events are caught here and logged centrally',
        #                     event_pattern=events.EventPattern(
        #                         detail={"stripeEvent": ["customer.subscription.created"]},
        #                         source=["stripeWebHookHandler.lambda"]
        #                     ))
