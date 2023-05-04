import { Construct } from 'constructs';
import { aws_events_targets, aws_lambda } from 'aws-cdk-lib';
import * as path from 'path';
import { ISecurityGroup, IVpc, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { ILayerVersion } from 'aws-cdk-lib/aws-lambda';

export interface BclConvertProps {
  layers: ILayerVersion[],
  securityGroups: ISecurityGroup[],
  vpc: IVpc,
  mainBus: IEventBus,
  functionName: string,
}

export class BclConvertConstruct extends Construct {

  constructor(scope: Construct, id: string, props: BclConvertProps) {
    super(scope, id);

    const bclConvertLambda = new aws_lambda.Function(this, 'BclConvertFunction', {
      runtime: aws_lambda.Runtime.PYTHON_3_9,
      code: aws_lambda.Code.fromAsset(path.join(__dirname, 'runtime/')),
      handler: 'handler',
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: props.securityGroups,
      layers: props.layers,
      functionName: props.functionName,
      environment: {
        EVENT_BUS_NAME: props.mainBus.eventBusName,
      },
    });

    props.mainBus.grantPutEventsTo(bclConvertLambda);

    // ---

    // TODO also consider Aspect to cross cut creating "the same Rule for multiple consumers" scenario

    const bclConvertEventRule = new Rule(this, 'BclConvertEventRule', {
      ruleName: 'BclConvertEventRule',
      description: 'Rule to send {event_type.value} events to the {handler.function_name} Lambda',
      eventBus: props.mainBus,
    });

    bclConvertEventRule.addTarget(new aws_events_targets.LambdaFunction(bclConvertLambda));
    bclConvertEventRule.addEventPattern({
      source: ['ORCHESTRATOR'],  // FIXME how to impl? how to share a "code construct" between TS and Py... One way is jsii
      detailType: ['SequenceRunStateChange'],
    });
  }
}
