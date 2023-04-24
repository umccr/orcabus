import * as cdk from 'aws-cdk-lib';
import { aws_ec2 } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EventBus } from 'aws-cdk-lib/aws-events';
import { getVpc } from './stateful/vpc/component';
import { SecurityGroupConstruct } from './stateful/securitygroup/component';
import { EventBusConstruct } from './stateful/eventbridge/component';
import { LambdaLayerConstruct } from './stateless/layers/component';
import { BclConvertConstruct } from './stateless/bcl_convert/component';
import {MultiSchemaConstructProps, MultiSchemaConstruct} from "./stateless/schema/component";
import {Props as SchemaRegistryProps} from "./stateful/schemaregistry/component";

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps,
}


export class OrcaBusStatelessStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatelessConfig) {
    super(scope, id, props);

    // --- Constructs from Stateful stack or pre-existing resources

    const vpc = getVpc(this);

    const securityGroups = [
      aws_ec2.SecurityGroup.fromLookupByName(
        this,
        'BclConvertLambdaSg',
        SecurityGroupConstruct.ORCABUS_LAMBDA_SECURITY_GROUP,  // FIXME externalise config
        vpc,
      ),
    ];

    const mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', EventBusConstruct.MAIN_BUS);  // FIXME externalise config


    new MultiSchemaConstruct(this, 'MultiSchema', props.multiSchemaConstructProps)

    // --- Create Stateless resources

    // TODO
    //  here is our layer deps dirs
    //  for each dir, create LambdaLayerConstruct
    //  optionally, a flag to say, whether to build the assert or, not

    const lambdaLayerConstruct = new LambdaLayerConstruct(this, 'LambdaLayerConstruct');
    const layers = [lambdaLayerConstruct.eb_util, lambdaLayerConstruct.schema];

    new BclConvertConstruct(this, 'BclConvertConstruct', { layers, securityGroups, vpc, mainBus });
  }
}
