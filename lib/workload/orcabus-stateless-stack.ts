import * as cdk from 'aws-cdk-lib';
import { aws_lambda } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { MultiSchemaConstructProps } from './stateless/schema/component';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { Filemanager } from './stateful/filemanager/deploy/lib/filemanager';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps;
  eventBusName: string;
  lambdaSecurityGroupName: string;
  lambdaRuntimePythonVersion: aws_lambda.Runtime;
  bclConvertFunctionName: string;
  rdsMasterSecretName: string;
}

export class OrcaBusStatelessStack extends cdk.Stack {
  private vpc: IVpc;
  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatelessConfig) {
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

    this.createFilemanager();
  }

  private createSequenceRunManager() {
    // TODO new SequenceRunManagerConstruct() from lib/workload/stateless/sequence_run_manager/deploy/component.ts
    //   However, the implementation is still incomplete...
  }

  private createFilemanager() {
    // todo, implement after https://github.com/umccr/orcabus/issues/86
    // new Filemanager(
    //   this,
    //   "Filemanager",
    //   {
    //     buckets: [],
    //     buildEnvironment: {},
    //     database: undefined,
    //     eventSources: [],
    //     migrateDatabase: false,
    //     onFailure: undefined,
    //     rustLog: '',
    //     vpc: undefined
    //   }
    // );
  }
}
