#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.orcabus_stack import OrcaBusStack
from stacks.schema_stack import SchemaStack

account_id = os.environ.get("CDK_DEFAULT_ACCOUNT")
aws_region = os.environ.get("CDK_DEFAULT_REGION")
aws_env = {
    "account": account_id,
    "region": aws_region,
}

props = {
    "namespace": "OrcaBus",
}

app = cdk.App()

SchemaStack(
    scope=app,
    construct_id=f"{props['namespace']}SchemaStack",
    props=props,
    env=aws_env,
)

OrcaBusStack(
    scope=app,
    construct_id=props["namespace"],
    props=props,
    env=aws_env,
)

tags = {
    "Stack": props["namespace"],
    "Creator": "cdk",
    "Environment": account_id,
}

for k, v in tags.items():
    cdk.Tags.of(app).add(key=k, value=v)

app.synth()
