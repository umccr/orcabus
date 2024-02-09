import * as cdk from 'aws-cdk-lib';
import { aws_lambda } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { MultiSchemaConstructProps } from './stateless/schema/component';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { OrcaBusStatefulStack } from './orcabus-stateful-stack';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps;
  eventBusName: string;
  lambdaSecurityGroupName: string;
  lambdaRuntimePythonVersion: aws_lambda.Runtime;
  bclConvertFunctionName: string;
  rdsMasterSecretName: string;
}

/**
 * The stateless stack depends on the stateful stack. Note, this could be restricted further
 * so that not all of the stateful stack is passed to the stateless stack. E.g. for filemanager,
 * instead of passing the whole stack, it could just be the `IQueue` that filemanager depends on.
 *
 * See for reference:
 * https://blog.serverlessadvocate.com/serverless-aws-cdk-pipeline-best-practices-patterns-part-1-ab80962f109d#1913
 */
export interface StatefulStackDependency {
  /**
   * The stateful stack which the stateless stack depends on.
   */
  statefulStack: OrcaBusStatefulStack;
}

export class OrcaBusStatelessStack extends cdk.Stack {
  private vpc: IVpc;
  constructor(
    scope: Construct,
    id: string,
    props: cdk.StackProps & OrcaBusStatelessConfig & StatefulStackDependency
  ) {
    super(scope, id, props);

    // --- Constructs from Stateful stack or pre-existing resources

    this.vpc = getVpc(this);

    // const securityGroups = [
    //   aws_ec2.SecurityGroup.fromLookupByName(
    //     this,
    //     'LambdaSecurityGroup',
    //     props.lambdaSecurityGroupName,
    //     vpc
    //   ),
    // ];

    // const mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    // --- Create Stateless resources

    // new MultiSchemaConstruct(this, 'MultiSchema', props.multiSchemaConstructProps);

    // hook microservice construct components here
    this.createSequenceRunManager();
  }

  private createSequenceRunManager() {
    // TODO new SequenceRunManagerConstruct() from lib/workload/stateless/sequence_run_manager/deploy/component.ts
    //   However, the implementation is still incomplete...
  }
}
