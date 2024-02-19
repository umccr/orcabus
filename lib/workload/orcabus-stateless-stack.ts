import * as cdk from 'aws-cdk-lib';
import { Arn, aws_lambda } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { MultiSchemaConstructProps } from './stateless/schema/component';
import { IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Filemanager } from './stateless/filemanager/deploy/lib/filemanager';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps;
  eventBusName: string;
  lambdaSecurityGroupName: string;
  lambdaRuntimePythonVersion: aws_lambda.Runtime;
  bclConvertFunctionName: string;
  rdsMasterSecretName: string;
  filemanagerDependencies?: FilemanagerDependencies;
}

export interface FilemanagerDependencies {
  /**
   * Queue name used by the EventSource construct.
   */
  eventSourceQueueName: string;
  /**
   * Buckets defined by the EventSource construct.
   */
  eventSourceBuckets: string[];
  /**
   * Database secret name for the filemanager.
   */
  databaseSecretName: string;
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

    if (props.filemanagerDependencies) {
      this.createFilemanager({
        ...props.filemanagerDependencies,
        lambdaSecurityGroupName: props.lambdaSecurityGroupName,
      });
    }
  }

  private createSequenceRunManager() {
    // TODO new SequenceRunManagerConstruct() from lib/workload/stateless/sequence_run_manager/deploy/component.ts
    //   However, the implementation is still incomplete...
  }

  private createFilemanager(
    dependencies: FilemanagerDependencies & { lambdaSecurityGroupName: string }
  ) {
    // Opting to reconstruct the dependencies here, and pass them into the service as constructs.
    const queue = Queue.fromQueueArn(
      this,
      'FilemanagerQueue',
      Arn.format(
        {
          resource: dependencies.eventSourceQueueName,
          service: 'Queue',
        },
        this
      )
    );
    const databaseSecurityGroup = SecurityGroup.fromLookupByName(
      this,
      'FilemanagerDatabaseSecurityGroup',
      dependencies.lambdaSecurityGroupName,
      this.vpc
    );
    const databaseSecret = Secret.fromSecretNameV2(
      this,
      'FilemanagerDatabaseSecret',
      dependencies.databaseSecretName
    );

    new Filemanager(this, 'Filemanager', {
      buckets: dependencies.eventSourceBuckets,
      buildEnvironment: {},
      databaseSecret,
      databaseSecurityGroup,
      eventSources: [queue],
      migrateDatabase: true,
      vpc: this.vpc,
    });
  }
}
