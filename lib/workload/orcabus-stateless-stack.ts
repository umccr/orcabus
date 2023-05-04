import * as cdk from 'aws-cdk-lib';
import { aws_ec2 } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EventBus } from 'aws-cdk-lib/aws-events';
import { getVpc } from './stateful/vpc/component';
import { LambdaLayerConstruct } from './stateless/layers/component';
import { BclConvertConstruct, BclConvertProps } from './stateless/bcl_convert/component';
import { MultiSchemaConstruct, MultiSchemaConstructProps } from './stateless/schema/component';
import { OrcaBusStatefulConfig } from './orcabus-stateful-stack';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps,
  bclConvertFunctionName: string,
}


export class OrcaBusStatelessStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatelessConfig & OrcaBusStatefulConfig) {
    super(scope, id, props);

    // --- Constructs from Stateful stack or pre-existing resources

    const vpc = getVpc(this);

    const securityGroups = [
      aws_ec2.SecurityGroup.fromLookupByName(
        this,
        'LambdaSecurityGroup',
        props.securityGroupProps.securityGroupName,
        vpc,
      ),
    ];

    const mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusProps.eventBusName);

    // --- Create Stateless resources

    new MultiSchemaConstruct(this, 'MultiSchema', props.multiSchemaConstructProps);

    // TODO
    //  here is our layer deps dirs
    //  for each dir, create LambdaLayerConstruct
    //  optionally, a flag to say, whether to build the assert or, not

    const lambdaLayerConstruct = new LambdaLayerConstruct(this, 'LambdaLayerConstruct');
    const layers = [lambdaLayerConstruct.eb_util, lambdaLayerConstruct.schema];

    const bclConvertProps: BclConvertProps = {
      mainBus: mainBus,
      layers: layers,
      securityGroups: securityGroups,
      vpc: vpc,
      functionName: props.bclConvertFunctionName,
    };
    new BclConvertConstruct(this, 'BclConvertConstruct', bclConvertProps);
  }
}
