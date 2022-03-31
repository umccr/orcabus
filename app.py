#!/usr/bin/env python3
from constructs import Construct
import aws_cdk as cdk

from stacks.orcabus_stack import OrcabusStack
from stacks.schema_stack import SchemaStack
from stacks.icav1_stack import ICAV1Stack

props = {
    'namespace': 'orcabus'
}

app = cdk.App(
    context={
        "props": props
    }
)

# Bring up the organization event bus
orcabus_stack = OrcabusStack(scope=app,
                             construct_id=props['namespace'])

# ICAV1 stack
icav1_stack = ICAV1Stack(
    scope=app,
    construct_id=f"{props['namespace']}ICAV1Stack",
    orcabus_stack=orcabus_stack
)

SchemaStack(scope=app,
            construct_id=f"{props['namespace']}SchemaStack",
            props=props)

app.synth()
