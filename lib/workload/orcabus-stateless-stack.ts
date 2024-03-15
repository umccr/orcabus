import * as cdk from 'aws-cdk-lib';
import { Arn, aws_ssm } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { getVpc } from './stateful/vpc/component';
import { MultiSchemaConstructProps } from './stateless/schema/component';
import { IVpc, ISecurityGroup, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Filemanager } from './stateless/filemanager/deploy/lib/filemanager';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import {
  PostgresManagerStack,
  PostgresManagerConfig,
} from './stateless/postgres_manager/deploy/postgres-manager-stack';
import { SequenceRunManagerStack } from './stateless/sequence_run_manager/deploy/component';
import { EventBus, IEventBus } from 'aws-cdk-lib/aws-events';
import * as param from '../../config/param';
import { IHttpApi, HttpApiAttributes, HttpStage, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';

export interface OrcaBusStatelessConfig {
  multiSchemaConstructProps: MultiSchemaConstructProps;
  eventBusName: string;
  lambdaSecurityGroupName: string;
  rdsMasterSecretName: string;
  postgresManagerConfig: PostgresManagerConfig;
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
  private readonly vpc: IVpc;
  private readonly lambdaSecurityGroup: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly sharedHttpApi: IHttpApi;

  // microservice stacks
  microserviceStackArray: cdk.Stack[] = [];

  constructor(scope: Construct, id: string, props: cdk.StackProps & OrcaBusStatelessConfig) {
    super(scope, id, props);

    // --- Constructs from Stateful stack or pre-existing resources

    this.vpc = getVpc(this);

    this.lambdaSecurityGroup = SecurityGroup.fromLookupByName(
      this,
      'OrcaBusLambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
    );

    this.mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    // You may reuse the shared HttpApi Gateway if you prefer. Doing so, please use the namespace
    // in the route path prefix. You can pass along `this.sharedHttpApi` through your stack props.
    const sharedHttpApiId = aws_ssm.StringParameter.valueFromLookup(this, param.SHARED_HTTP_API_ID);
    const sharedHttpApiAttributes: HttpApiAttributes = { httpApiId: sharedHttpApiId };
    this.sharedHttpApi = HttpApi.fromHttpApiAttributes(
      this,
      'OrcaBusSharedHttpApi',
      sharedHttpApiAttributes
    );
    new HttpStage(this, 'OrcaBusSharedHttpApiStage', { httpApi: this.sharedHttpApi });

    // --- Create Stateless resources

    // new MultiSchemaConstruct(this, 'MultiSchema', props.multiSchemaConstructProps);

    // hook microservice construct components here

    this.microserviceStackArray.push(this.createSequenceRunManager());
    this.microserviceStackArray.push(this.createPostgresManager(props.postgresManagerConfig));

    if (props.filemanagerDependencies) {
      this.createFilemanager({
        ...props.filemanagerDependencies,
        lambdaSecurityGroupName: props.lambdaSecurityGroupName,
      });
    }
  }

  private createSequenceRunManager() {
    return new SequenceRunManagerStack(this, 'SequenceRunManager', {
      securityGroups: [this.lambdaSecurityGroup],
      vpc: this.vpc,
      mainBus: this.mainBus,
      httpApi: this.sharedHttpApi,
    });
  }

  private createPostgresManager(config: PostgresManagerConfig) {
    return new PostgresManagerStack(this, 'PostgresManager', {
      ...config,
      vpc: this.vpc,
      lambdaSecurityGroup: this.lambdaSecurityGroup,
    });
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
          service: 'sqs',
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

    return new Filemanager(this, 'Filemanager', {
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
