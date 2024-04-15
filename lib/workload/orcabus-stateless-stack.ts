import * as cdk from 'aws-cdk-lib';
import { Arn } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './components/vpc';
import { MultiSchemaConstructProps } from './stateless/schema/component';
import { IVpc, ISecurityGroup, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Filemanager, FilemanagerConfig } from './stateless/filemanager/deploy/lib/filemanager';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import {
  PostgresManagerStack,
  PostgresManagerConfig,
} from './stateless/postgres_manager/deploy/postgres-manager-stack';
import {
  MetadataManagerStack,
  MetadataManagerConfig,
} from './stateless/metadata_manager/deploy/stack';
import { SequenceRunManagerStack } from './stateless/sequence_run_manager/deploy/component';
import { EventBus, IEventBus } from 'aws-cdk-lib/aws-events';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps;
  eventBusName: string;
  computeSecurityGroupName: string;
  rdsMasterSecretName: string;
  postgresManagerConfig: PostgresManagerConfig;
  metadataManagerConfig: MetadataManagerConfig;
  filemanagerConfig: FilemanagerConfig;
}

export class OrcaBusStatelessStack extends cdk.Stack {
  private readonly vpc: IVpc;
  private readonly lambdaSecurityGroup: ISecurityGroup;
  private readonly mainBus: IEventBus;

  // microservice stacks
  microserviceStackArray: cdk.Stack[] = [];

  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatelessConfig) {
    super(scope, id, props);

    // --- Constructs from Stateful stack or pre-existing resources

    this.vpc = getVpc(this);

    this.lambdaSecurityGroup = SecurityGroup.fromLookupByName(
      this,
      'OrcaBusLambdaSecurityGroup',
      props.computeSecurityGroupName,
      this.vpc
    );

    this.mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    // --- Create Stateless resources

    // new MultiSchemaConstruct(this, 'MultiSchema', props.multiSchemaConstructProps);

    // hook microservice construct components here

    this.microserviceStackArray.push(this.createSequenceRunManager(props));
    this.microserviceStackArray.push(this.createPostgresManager(props.postgresManagerConfig));
    this.microserviceStackArray.push(this.createMetadataManager(props.metadataManagerConfig));
    this.microserviceStackArray.push(this.createFilemanager(props.filemanagerConfig));
  }

  private createSequenceRunManager(props: cdk.StackProps) {
    return new SequenceRunManagerStack(this, 'SequenceRunManager', {
      securityGroups: [this.lambdaSecurityGroup],
      vpc: this.vpc,
      mainBus: this.mainBus,
      ...props,
    });
  }

  private createPostgresManager(config: PostgresManagerConfig) {
    return new PostgresManagerStack(this, 'PostgresManager', {
      ...config,
      vpc: this.vpc,
      lambdaSecurityGroup: this.lambdaSecurityGroup,
    });
  }

  private createMetadataManager(config: MetadataManagerConfig) {
    return new MetadataManagerStack(this, 'MetadataManager', {
      vpc: this.vpc,
      lambdaSecurityGroups: this.lambdaSecurityGroup,
      ...config,
    });
  }

  private createFilemanager(config: FilemanagerConfig) {
    // Opting to reconstruct the dependencies here, and pass them into the service as constructs.
    const queue = Queue.fromQueueArn(
      this,
      'FilemanagerQueue',
      Arn.format(
        {
          resource: config.eventSourceQueueName,
          service: 'sqs',
        },
        this
      )
    );

    return new Filemanager(this, 'Filemanager', {
      buckets: config.eventSourceBuckets,
      buildEnvironment: {},
      databaseClusterEndpointHostParameter: config.databaseClusterEndpointHostParameter,
      port: config.port,
      securityGroup: this.lambdaSecurityGroup,
      eventSources: [queue],
      migrateDatabase: true,
      vpc: this.vpc,
    });
  }
}
