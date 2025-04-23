import path from 'path';
import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { FilemanagerToolsPythonLambdaLayer } from '../../../../components/python-filemanager-tools-layer';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import {
  DefinitionBody,
  IStateMachine,
  LogLevel,
  StateMachineType,
} from 'aws-cdk-lib/aws-stepfunctions';
import { MetadataToolsPythonLambdaLayer } from '../../../../components/python-metadata-tools-layer';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import { WorkflowToolsPythonLambdaLayer } from '../../../../components/python-workflow-tools-layer';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import {
  AthenaWithBucketProps,
  DataPackageReportOutputProps,
  DataPackagingStateMachineFunctionProps,
  DataPresigningStateMachineFunctionProps,
  DataPushICAv2StateMachineFunctionProps,
  DataPushS3StateMachineFunctionProps,
  DataPushStateMachineFunctionProps,
  DataSharingStackConfig,
  ecsTaskProps,
  LambdaApiFunctionProps,
  LambdaFunctionProps,
  LambdaLayerList,
  LambdaLayerToFunctionMapping,
  LambdaNameList,
  lambdaObject,
  lambdaObjectProps,
} from './interfaces';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import { ContainerInsights } from 'aws-cdk-lib/aws-ecs';
import * as ecrAssets from 'aws-cdk-lib/aws-ecr-assets';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import * as awsLogs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { NagSuppressions } from 'cdk-nag';
import { ApiGatewayConstruct } from '../../../../components/api-gateway';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  HttpMethod,
  HttpNoneAuthorizer,
  HttpRoute,
  HttpRouteKey,
} from 'aws-cdk-lib/aws-apigatewayv2';
import * as s3 from 'aws-cdk-lib/aws-s3';

// Some globals
export type DataSharingStackProps = DataSharingStackConfig & cdk.StackProps;

export class DataSharingStack extends Stack {
  public readonly lambdaLayerPrefix: string = 'ds'; // Data Sharing
  public lambdaLayers: { [key in LambdaLayerList]: PythonLayerVersion };
  public lambdaObjects: { [key in LambdaNameList]: lambdaObject } = {} as {
    [key in LambdaNameList]: lambdaObject;
  };
  public readonly API_VERSION: string = 'v1';

  constructor(scope: Construct, id: string, props: StackProps & DataSharingStackProps) {
    super(scope, id, props);

    // Get the bucket object
    const packagingLookUpBucket = Bucket.fromBucketName(
      this,
      's3-sharing-bucket',
      props.packagingLookUpBucketName
    );

    // Get the databases
    const packagingDynamoDbApiTable = dynamodb.TableV2.fromTableName(
      this,
      'packagingDynamoDbApiTable',
      props.packagingDynamoDbApiTableName
    );
    const pushJobDynamoDbApiTable = dynamodb.TableV2.fromTableName(
      this,
      'pushJobDynamoDbApiTable',
      props.pushJobDynamoDbApiTableName
    );

    // Get the lookup table that the packaging application uses as a cache
    const packagingLookUpDynamoDbTable = dynamodb.TableV2.fromTableName(
      this,
      'packagingLookUpDynamoDbTable',
      props.packagingLookUpDynamoDbTableName
    );

    // Get the event bus as an object
    const eventBus = events.EventBus.fromEventBusName(this, 'eventBus', props.eventBusName);

    // Create the tool layers
    this.createToolLayers();

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      props.hostedZoneNameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      props.orcabusTokenSecretsManagerPath
    );

    /*
    Get the s3 steps copy bucket
    */
    const s3CopyStepsBucket = s3.Bucket.fromBucketName(
      this,
      's3StepsCopyBucket',
      props.s3StepsCopyProps.s3StepsCopyBucketName
    );

    const athenaS3Bucket = s3.Bucket.fromBucketName(
      this,
      'athenaBucket',
      props.athenaProps.athenaS3BucketName
    );

    const athenaFunction = lambda.Function.fromFunctionName(
      this,
      'athenaFunction',
      props.athenaProps.athenaLambdaFunctionName
    );

    const athenaProps: AthenaWithBucketProps = {
      ...props.athenaProps,
      athenaS3Bucket: athenaS3Bucket,
      athenaLambdaFunction: athenaFunction,
    };

    // Create the lambda functions
    this.createLambdaFunctions({
      // Standard props
      hostnameSsmParameterObject: hostnameSsmParameterObj,
      orcabusTokenSecretObject: orcabusTokenSecretObj,
      // DynamoDB tables
      packagingDynamoDbLookUpTable: packagingLookUpDynamoDbTable,
      packagingDynamoDbTableIndexName: 'content',
      // Steps Bucket
      s3StepsCopyBucket: s3CopyStepsBucket,
      s3StepsCopyPrefix: props.s3StepsCopyProps.s3StepsCopyPrefix,
      // Packaging bucket
      packagingLookUpBucket: packagingLookUpBucket,
      packagingLookUpPrefix: props.packagingSharingPrefix,
      pushLogsPrefix: props.pushLogsPrefix,
      // Athena props
      athenaProps: athenaProps,
    });

    // Create the ECS task
    const dataPackageReportEcsTask = this.createDataReportEcsTask({
      packagingLookUpBucket: packagingLookUpBucket,
      packagingLookUpPrefix: props.packagingSharingPrefix,
      packagingLookUpDynamoDbTable: packagingLookUpDynamoDbTable,
      packagingLookUpDynamoDbTableIndexNames: props.packagingLookUpDynamoDbTableIndexNames,
    });

    // Create state machines
    const packagingStateMachine = this.createPackagingStateMachine({
      lambdas: this.lambdaObjects,
      packagingLookUpBucket: packagingLookUpBucket,
      packageLookUpDb: packagingLookUpDynamoDbTable,
      packageLookUpTableIndexes: props.packagingLookUpDynamoDbTableIndexNames,
      ecsTask: dataPackageReportEcsTask,
      eventBusProps: {
        eventBus: eventBus,
        eventSource: props.eventSource,
        fastqSyncEventDetailType: props.fastqSyncDetailType,
      },
    });

    // Create presigning state machine
    const presigningStateMachine = this.createPresigningStateMachine({
      lambdas: this.lambdaObjects,
      packagingLookUpBucket: packagingLookUpBucket,
      packagingLookUpDb: packagingLookUpDynamoDbTable,
      packagingLookUpDbIndexNames: props.packagingLookUpDynamoDbTableIndexNames,
    });

    // Create push state machines
    const pushStateMachine = this.createPushStateMachines({
      lambdas: this.lambdaObjects,
      icav2DataPushStateMachineProps: {
        lambdas: this.lambdaObjects,
        eventBusProps: {
          eventBus: eventBus,
          eventSource: props.eventSource,
          icav2JobCopyEventDetailType: props.icav2JobCopyDetailType,
        },
      },
      s3DataPushStateMachineProps: {
        lambdas: this.lambdaObjects,
        s3StepsCopyProps: {
          s3StepsCopyBucketName: props.s3StepsCopyProps.s3StepsCopyBucketName,
          s3StepsCopyPrefix: props.s3StepsCopyProps.s3StepsCopyPrefix,
          s3StepsFunctionArn: props.s3StepsCopyProps.s3StepsFunctionArn,
        },
      },
    });

    // Create api lambda function
    const apiLambdaFunction = this.createLambdaApiFunction({
      // Layers
      dataSharingLayer: this.lambdaLayers.dataSharingToolsLayer,
      fileManagerLayer: this.lambdaLayers.fileManagerLayer,
      // SSM And Secrets
      orcabusTokenSecretObj: orcabusTokenSecretObj,
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      customDomainNamePrefix: props.apiGatewayCognitoProps.customDomainNamePrefix,
      // Step functions
      packagingStateMachine: packagingStateMachine,
      presigningStateMachine: presigningStateMachine,
      pushStateMachine: pushStateMachine,
      // Buckets
      packagingLookUpBucket: packagingLookUpBucket,
      packagingLookUpPrefix: props.packagingSharingPrefix,
      // Event stuff
      eventBus: eventBus,
      eventSource: props.eventSource,
      eventDetailTypes: props.eventDetailTypes,
      // Tables
      packagingDynamoDbApiTable: packagingDynamoDbApiTable,
      pushJobDynamoDbApiTable: pushJobDynamoDbApiTable,
      // Table indexes
      packagingDynamoDbTableIndexNames: props.packagingLookUpDynamoDbTableIndexNames,
      pushJobDynamoDbTableIndexNames: props.pushJobDynamoDbTableIndexNames,
    });

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiLambdaFunction);

    this.add_http_routes(apiGateway, apiIntegration);
  }

  private camelCaseToSnakeCase(camelCase: string): string {
    return camelCase.replace(/([A-Z])/g, '_$1').toLowerCase();
  }

  private createToolLayers() {
    // Create the layers
    this.lambdaLayers = {
      fileManagerLayer: new FilemanagerToolsPythonLambdaLayer(this, 'filemanager-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      metadataLayer: new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      workflowManagerLayer: new WorkflowToolsPythonLambdaLayer(this, 'workflow-manager-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      fastqToolsLayer: new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
        layerPrefix: this.lambdaLayerPrefix,
      }).lambdaLayerVersionObj,
      dataSharingToolsLayer: new PythonLambdaLayerConstruct(this, 'data-sharing-tools-layer', {
        layerName: 'dataSharingToolsLayer',
        layerDescription: 'layer to add in some functions on interacting with the package database',
        layerDirectory: path.join(__dirname, '../layers/data_sharing_tools_layer'),
      }).lambdaLayerVersionObj,
    };
  }

  private createSfnLambdaObject(lambdaObject: lambdaObjectProps): lambdaObject {
    const lambdaNameToSnakeCase = this.camelCaseToSnakeCase(lambdaObject.name);

    const lambdaFunction = new PythonUvFunction(this, lambdaObject.name, {
      entry: path.join(__dirname, '../lambdas', lambdaNameToSnakeCase + '_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: lambdaNameToSnakeCase + '.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      layers: lambdaObject.lambdaLayers,
    });

    return {
      name: lambdaObject.name,
      lambdaLayers: lambdaObject.lambdaLayers,
      lambdaFunction: lambdaFunction,
    };
  }

  private createDataReportEcsTask(props: ecsTaskProps): DataPackageReportOutputProps {
    const vpc = ec2.Vpc.fromLookup(this, 'MainVpc', {
      vpcName: 'main-vpc',
    });
    const cluster = new ecs.Cluster(this, 'FargateCluster', {
      vpc: vpc,
      enableFargateCapacityProviders: true,
      containerInsightsV2: ContainerInsights.ENABLED,
    });
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'FargateTaskDefinition', {
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
      cpu: 8192, // Maps to 8 CPUs, we're running R after all
      // For 8 CPU:
      // Available memory values:
      //    Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB)
      memoryLimitMiB: 16384,
    });
    // We also need a security group context to run the task in
    const securityGroup = new ec2.SecurityGroup(this, 'SecurityGroup', {
      vpc,
    });

    // Generate the docker image asset
    const architecture = lambda.Architecture.ARM_64;

    // Add container to task role
    const dataSummaryReportContainer = taskDefinition.addContainer('dataSummaryReportContainer', {
      image: ecs.ContainerImage.fromDockerImageAsset(
        new ecrAssets.DockerImageAsset(this, 'data_summary_reporter', {
          directory: path.join(__dirname, '../ecs/tasks/generate_data_summary_report'),
          buildArgs: {
            TARGETPLATFORM: architecture.dockerPlatform,
          },
        })
      ),
      containerName: `dataSummaryReportContainer`,
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'dataSummaryReportContainer',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Give permissions to the container to access the packaging bucket
    props.packagingLookUpBucket.grantReadWrite(
      taskDefinition.taskRole,
      `${props.packagingLookUpPrefix}*`
    );

    // Give permissions to the container to access the packaging dynamodb table
    props.packagingLookUpDynamoDbTable.grantReadData(taskDefinition.taskRole);

    // Give permissions to the container to access the table index
    // Grant query permissions on indexes
    const packaging_index_arn_list: string[] = props.packagingLookUpDynamoDbTableIndexNames.map(
      (index_name) => {
        return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingLookUpDynamoDbTable.tableName}/index/${index_name}-index`;
      }
    );
    taskDefinition.addToTaskRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: packaging_index_arn_list,
      })
    );

    // Add in nag suppression for the task role
    NagSuppressions.addResourceSuppressions(
      taskDefinition,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Task needs read permissions to the bucket with a prefix, so this is obviously going to contain a wild card',
        },
      ],
      true
    );

    return {
      cluster: cluster,
      taskDefinition: taskDefinition,
      container: dataSummaryReportContainer,
      securityGroup: securityGroup,
    };
  }

  private createPackagingStateMachine(
    props: DataPackagingStateMachineFunctionProps
  ): IStateMachine {
    // Create the aws step function
    const packagingStateMachine = new sfn.StateMachine(this, 'dataPackagingSfn', {
      // State Machine Name
      stateMachineName: 'data-sharing-packager-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/packaging_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        // Our data sharing bucket with our report and download scripts
        __sharing_bucket__: props.packagingLookUpBucket.bucketName,
        // Table
        __dynamodb_table_name__: props.packageLookUpDb.tableName,
        // Event handling
        __event_bus_name__: props.eventBusProps.eventBus.eventBusName,
        __event_source__: props.eventBusProps.eventSource,
        __fastq_sync_detail_type__: props.eventBusProps.fastqSyncEventDetailType,
        // Data summary reporter substitutions
        __generate_data_package_report_task_definition_arn__:
          props.ecsTask.taskDefinition.taskDefinitionArn,
        __generate_data_package_report_container_name__: props.ecsTask.container.containerName,
        __generate_data_package_report_cluster_arn__: props.ecsTask.cluster.clusterArn,
        __security_group__: props.ecsTask.securityGroup.securityGroupId,
        __subnets__: props.ecsTask.cluster.vpc.privateSubnets
          .map((subnet) => subnet.subnetId)
          .join(','),
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: keyof typeof props.lambdas;
    for (lambdaName in props.lambdas) {
      props.lambdas[lambdaName].lambdaFunction.currentVersion.grantInvoke(packagingStateMachine);
    }

    // Packaging state machine also needs access to the table
    props.packageLookUpDb.grantReadWriteData(packagingStateMachine);

    // Grant query permissions on indexes
    const packaging_index_arn_list: string[] = props.packageLookUpTableIndexes.map((index_name) => {
      return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packageLookUpDb.tableName}/index/${index_name}-index`;
    });
    packagingStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: packaging_index_arn_list,
      })
    );

    // Packager requires permissions to run the ECS task
    props.ecsTask.taskDefinition.grantRun(packagingStateMachine);

    // Packager requires permissions to listen to the ecs task completion
    packagingStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Packager requires permissions to execute itself
    // Because this steps execution uses a distributed map in its step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    // packagingStateMachine.grantStartExecution(packagingStateMachine);
    const distributedMapPolicy = new iam.Policy(this, 'sfn-distributed-map-policy', {
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            resources: [packagingStateMachine.stateMachineArn],
            actions: ['states:StartExecution'],
          }),
          new iam.PolicyStatement({
            resources: [
              `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:execution:${packagingStateMachine.stateMachineName}/*:*`,
            ],
            actions: ['states:RedriveExecution'],
          }),
        ],
      }),
    });
    // Add the policy to the state machine role
    packagingStateMachine.role.attachInlinePolicy(distributedMapPolicy);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    packagingStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Grant permissions to push to the event bus
    props.eventBusProps.eventBus.grantPutEventsTo(packagingStateMachine);

    NagSuppressions.addResourceSuppressions(
      [packagingStateMachine, distributedMapPolicy],
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Packaging statemachine needs wild card permissions on itself because of the distributed map nature of the state machine',
        },
      ],
      true
    );

    return packagingStateMachine;
  }

  private createPresigningStateMachine(
    props: DataPresigningStateMachineFunctionProps
  ): IStateMachine {
    // Create the aws step function
    const presigningStateMachine = new sfn.StateMachine(this, 'presigningStateMachineSfn', {
      // State Machine Name
      stateMachineName: 'data-sharing-presigner-express-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/presigning_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        // Our data sharing bucket with our report and download scripts
        __sharing_bucket__: props.packagingLookUpBucket.bucketName,
        // Table
        __dynamodb_table_name__: props.packagingLookUpDb.tableName,
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
      // This is an express workflow
      stateMachineType: StateMachineType.EXPRESS,
      // Enable logging on the state machine
      logs: {
        level: LogLevel.ALL,
        // Create a new log group for the state machine
        destination: new awsLogs.LogGroup(this, 'dataPackaging-presigning', {
          retention: RetentionDays.ONE_DAY,
        }),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: keyof typeof props.lambdas;
    for (lambdaName in props.lambdas) {
      props.lambdas[lambdaName].lambdaFunction.currentVersion.grantInvoke(presigningStateMachine);
    }

    // Packaging state machine also needs access to the table
    props.packagingLookUpDb.grantReadWriteData(presigningStateMachine);

    // Allow the statemachine access to the dynamodb indexes
    const packaging_index_arn_list: string[] = props.packagingLookUpDbIndexNames.map(
      (index_name) => {
        return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingLookUpDb.tableName}/index/${index_name}-index`;
      }
    );

    presigningStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: packaging_index_arn_list,
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      presigningStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'express sfn with logs',
        },
      ],
      true
    );

    return presigningStateMachine;
  }

  private createIcav2PushStateMachine(
    props: DataPushICAv2StateMachineFunctionProps
  ): IStateMachine {
    const icav2PushStateMachine = new sfn.StateMachine(this, 'dataPushIcav2StateMachine', {
      // State Machine Name
      stateMachineName: 'data-sharing-push-icav2-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/push_icav2_data_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        // Event stuff
        __event_bus_name__: props.eventBusProps.eventBus.eventBusName,
        __event_detail_type__: props.eventBusProps.icav2JobCopyEventDetailType,
        __event_source__: props.eventBusProps.eventSource,
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: keyof typeof props.lambdas;
    for (lambdaName in props.lambdas) {
      props.lambdas[lambdaName].lambdaFunction.currentVersion.grantInvoke(icav2PushStateMachine);
    }

    // Return the state machine
    return icav2PushStateMachine;
  }

  private createS3PushStateMachine(props: DataPushS3StateMachineFunctionProps): IStateMachine {
    const s3PushStateMachine = new sfn.StateMachine(this, 'dataPushs3StateMachine', {
      // State Machine Name
      stateMachineName: 'data-sharing-push-s3-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/push_s3_data_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        __aws_s3_copy_steps_bucket__: props.s3StepsCopyProps.s3StepsCopyBucketName,
        __aws_s3_copy_steps_prefix__: props.s3StepsCopyProps.s3StepsCopyPrefix,
        __aws_s3_steps_copy_sfn_arn__: props.s3StepsCopyProps.s3StepsFunctionArn,
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: keyof typeof props.lambdas;
    for (lambdaName in props.lambdas) {
      props.lambdas[lambdaName].lambdaFunction.currentVersion.grantInvoke(s3PushStateMachine);
    }

    // Give permissions to the s3 state machine to invoke the aws s3 steps copy function
    const awsS3StepsCopyFunction = sfn.StateMachine.fromStateMachineArn(
      this,
      's3-steps-copy-sfn',
      props.s3StepsCopyProps.s3StepsFunctionArn
    );

    // Grant permissions to the state machine
    awsS3StepsCopyFunction.grantStartExecution(s3PushStateMachine);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    s3PushStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Pusher requires permissions to execute itself
    // Because this steps execution uses a distributed map in its step function, we
    // have to wire up some extra permissions
    // Grant the state machine's role to execute itself
    // However we cannot just grant permission to the role as this will result in a circular dependency
    // between the state machine and the role
    // Instead we use the workaround here - https://github.com/aws/aws-cdk/issues/28820#issuecomment-1936010520
    // packagingStateMachine.grantStartExecution(packagingStateMachine);
    const distributedMapPolicy = new iam.Policy(this, 'push-sfn-distributed-map-policy', {
      document: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            resources: [s3PushStateMachine.stateMachineArn],
            actions: ['states:StartExecution'],
          }),
          new iam.PolicyStatement({
            resources: [
              `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:execution:${s3PushStateMachine.stateMachineName}/*:*`,
            ],
            actions: ['states:RedriveExecution'],
          }),
        ],
      }),
    });
    // Add the policy to the state machine role
    s3PushStateMachine.role.attachInlinePolicy(distributedMapPolicy);

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      [s3PushStateMachine, distributedMapPolicy],
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );
    return s3PushStateMachine;
  }

  private createPushStateMachines(props: DataPushStateMachineFunctionProps): IStateMachine {
    // We actually generate two sub state machines here
    // Then we create a parent state machine that will run either of the two sub state machines
    // Then after we wire up the permissions we return the parent state machine
    const icav2StateMachine = this.createIcav2PushStateMachine(
      props.icav2DataPushStateMachineProps
    );

    const s3StateMachine = this.createS3PushStateMachine(props.s3DataPushStateMachineProps);

    // Create the parent state machine
    const parentStateMachine = new sfn.StateMachine(this, 'dataPushStateMachine', {
      // State Machine Name
      stateMachineName: 'data-sharing-push-parent-sfn',
      // Definition
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, '../step_functions_templates/push_sfn_template.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        // Child step functions
        __icav2_data_push_sfn_arn__: icav2StateMachine.stateMachineArn,
        __s3_data_push_sfn_arn__: s3StateMachine.stateMachineArn,
        // All lambda substitutions
        ...this.createLambdaDefinitionSubstitutions(),
      },
    });

    // For all lambdas in the props.lambdaObjects, grant invoke permissions to the state machine
    let lambdaName: keyof typeof props.lambdas;
    for (lambdaName in props.lambdas) {
      props.lambdas[lambdaName].lambdaFunction.currentVersion.grantInvoke(parentStateMachine);
    }

    // Give parent state machine permissions to invoke the child state machines
    icav2StateMachine.grantStartExecution(parentStateMachine);
    s3StateMachine.grantStartExecution(parentStateMachine);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    parentStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      parentStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    return parentStateMachine;
  }

  private createLambdaFunctions(props: LambdaFunctionProps) {
    // Iterate over lambdaLayerToMapping and create the lambda functions
    let lambdaName: keyof typeof LambdaLayerToFunctionMapping;
    for (lambdaName in LambdaLayerToFunctionMapping) {
      const lambdaLayers = LambdaLayerToFunctionMapping[lambdaName].map((layerName) => {
        return this.lambdaLayers[layerName];
      });

      const lambdaObject = this.createSfnLambdaObject({
        name: lambdaName,
        lambdaLayers: lambdaLayers,
      });

      // Add environment variables
      lambdaObject.lambdaFunction.addEnvironment(
        'HOSTNAME_SSM_PARAMETER',
        props.hostnameSsmParameterObject.parameterName
      );
      lambdaObject.lambdaFunction.addEnvironment(
        'ORCABUS_TOKEN_SECRET_ID',
        props.orcabusTokenSecretObject.secretName
      );

      // Add permissions to the lambda function
      props.hostnameSsmParameterObject.grantRead(lambdaObject.lambdaFunction.currentVersion);
      props.orcabusTokenSecretObject.grantRead(lambdaObject.lambdaFunction.currentVersion);

      // Some lambdas need extra permissions or environment variables
      if (lambdaName == 'getS3DestinationAndSourceUriMappings') {
        lambdaObject.lambdaFunction.addEnvironment(
          'PACKAGING_TABLE_NAME',
          props.packagingDynamoDbLookUpTable.tableName
        );
        lambdaObject.lambdaFunction.addEnvironment(
          'CONTENT_INDEX_NAME',
          `${props.packagingDynamoDbTableIndexName}-index`
        );
        // Add read permissions policy
        props.packagingDynamoDbLookUpTable.grantReadData(
          lambdaObject.lambdaFunction.currentVersion
        );
        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          new iam.PolicyStatement({
            actions: ['dynamodb:Query'],
            resources: [
              `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingDynamoDbLookUpTable.tableName}/index/${props.packagingDynamoDbTableIndexName}-index`,
            ],
          })
        );
      }

      if (lambdaName == 'createCsvForS3StepsCopy') {
        // Lambda needs permissions to upload to the s3 bucket
        props.s3StepsCopyBucket.grantReadWrite(lambdaObject.lambdaFunction.currentVersion); //, `${props.s3StepsCopyPrefix}*`)
        // Lambda also needs permissions to know what AWS account it is running in
        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          new iam.PolicyStatement({
            actions: ['sts:GetCallerIdentity'],
            resources: ['*'],
          })
        );

        NagSuppressions.addResourceSuppressions(
          lambdaObject.lambdaFunction,
          [
            {
              id: 'AwsSolutions-IAM5',
              reason:
                'GetCallerIdentity is required to get the account id, resources is not relevant',
            },
          ],
          true
        );
      }

      if (lambdaName == 'createScriptFromPresignedUrlsList') {
        // Lambda needs permissions to upload to the s3 bucket
        props.packagingLookUpBucket.grantReadWrite(
          lambdaObject.lambdaFunction.currentVersion,
          `${props.packagingLookUpPrefix}*`
        );

        // Lambda needs permissions to read the packaging dynamodb table
        props.packagingDynamoDbLookUpTable.grantReadData(
          lambdaObject.lambdaFunction.currentVersion
        );

        // And we set the environment variable PACKAGING_TABLE_NAME to the table
        lambdaObject.lambdaFunction.addEnvironment(
          'PACKAGING_TABLE_NAME',
          props.packagingDynamoDbLookUpTable.tableName
        );
        lambdaObject.lambdaFunction.addEnvironment(
          'CONTENT_INDEX_NAME',
          `${props.packagingDynamoDbTableIndexName}-index`
        );

        // Lambda also needs permissions for the 'content' index since we will be picking up the presigned urls.
        // Hence we need to add the query permissions to the index
        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          new iam.PolicyStatement({
            actions: ['dynamodb:Query'],
            resources: [
              `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingDynamoDbLookUpTable.tableName}/index/content-index`,
            ],
          })
        );

        NagSuppressions.addResourceSuppressions(
          lambdaObject.lambdaFunction,
          [
            {
              id: 'AwsSolutions-IAM5',
              reason:
                'Lambda function needs access to the bucket prefix so this is obviously going to contain a wild card',
            },
          ],
          true
        );
      }

      if (lambdaName == 'uploadPushJobToS3') {
        // Lambda needs permissions to upload to the s3 bucket
        props.packagingLookUpBucket.grantReadWrite(
          lambdaObject.lambdaFunction.currentVersion,
          `${props.pushLogsPrefix}*`
        );

        // Lambda needs permissions to read the packaging dynamodb table
        props.packagingDynamoDbLookUpTable.grantReadData(
          lambdaObject.lambdaFunction.currentVersion
        );
        // And we set the environment variable PACKAGING_TABLE_NAME to the table
        lambdaObject.lambdaFunction.addEnvironment(
          'PACKAGING_TABLE_NAME',
          props.packagingDynamoDbLookUpTable.tableName
        );
        // We set the environment variable 'CONTENT_INDEX_NAME' to the index name
        lambdaObject.lambdaFunction.addEnvironment('CONTENT_INDEX_NAME', 'content-index');

        // Lambda also needs permissions for the 'content' index since we will be picking up the presigned urls.
        // Hence we need to add the query permissions to the index
        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          new iam.PolicyStatement({
            actions: ['dynamodb:Query'],
            resources: [
              `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingDynamoDbLookUpTable.tableName}/index/content-index`,
            ],
          })
        );

        NagSuppressions.addResourceSuppressions(
          lambdaObject.lambdaFunction,
          [
            {
              id: 'AwsSolutions-IAM5',
              reason:
                'Lambda function needs access to the bucket prefix so this is obviously going to contain a wild card',
            },
          ],
          true
        );
      }

      // For listPortalRunIdsInLibrary and getWorkflowFromPortalRunId we will need to add the athena
      // permissions to the lambda function
      if (lambdaName == 'listPortalRunIdsInLibrary' || lambdaName == 'getWorkflowFromPortalRunId') {
        lambdaObject.lambdaFunction.addEnvironment(
          'ATHENA_WORKGROUP_NAME',
          props.athenaProps.athenaWorkgroup
        );
        lambdaObject.lambdaFunction.addEnvironment(
          'ATHENA_DATASOURCE_NAME',
          props.athenaProps.athenaDataSource
        );
        lambdaObject.lambdaFunction.addEnvironment(
          'ATHENA_DATABASE_NAME',
          props.athenaProps.athenaDatabase
        );

        // Add athena permissions
        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          // From https://docs.aws.amazon.com/athena/latest/ug/example-policies-workgroup.html
          new iam.PolicyStatement({
            actions: [
              // Workgroup lists
              'athena:ListEngineVersions',
              'athena:ListWorkGroups',
              'athena:ListDataCatalogs',
              'athena:ListDatabases',
              'athena:GetDatabase',
              'athena:ListTableMetadata',
              'athena:GetTableMetadata',
              'athena:GetDataCatalog',
            ],
            resources: [`arn:aws:athena:${this.region}:${this.account}:*`],
          })
        );

        lambdaObject.lambdaFunction.currentVersion.addToRolePolicy(
          // From https://docs.aws.amazon.com/athena/latest/ug/example-policies-workgroup.html
          new iam.PolicyStatement({
            actions: [
              // Workgroup executions
              'athena:BatchGetQueryExecution',
              'athena:GetQueryExecution',
              'athena:ListQueryExecutions',
              'athena:StartQueryExecution',
              'athena:StopQueryExecution',
              'athena:GetQueryResults',
              'athena:GetQueryResultsStream',
              'athena:CreateNamedQuery',
              'athena:GetNamedQuery',
              'athena:BatchGetNamedQuery',
              'athena:ListNamedQueries',
              'athena:DeleteNamedQuery',
              'athena:CreatePreparedStatement',
              'athena:GetPreparedStatement',
              'athena:ListPreparedStatements',
              'athena:UpdatePreparedStatement',
              'athena:DeletePreparedStatement',
            ],
            resources: [
              `arn:aws:athena:${this.region}:${this.account}:workgroup/${props.athenaProps.athenaWorkgroup}`,
            ],
          })
        );

        // Allow read access to the athena output bucket
        props.athenaProps.athenaS3Bucket.grantReadWrite(
          lambdaObject.lambdaFunction.currentVersion,
          `${props.athenaProps.athenaS3Prefix}*`
        );

        props.athenaProps.athenaLambdaFunction.grantInvoke(
          lambdaObject.lambdaFunction.currentVersion
        );

        NagSuppressions.addResourceSuppressions(
          lambdaObject.lambdaFunction,
          [
            {
              id: 'AwsSolutions-IAM5',
              reason: 'Need access to all things athena',
            },
          ],
          true
        );
      }

      // Assign the lambda object to the lambdaObjects
      this.lambdaObjects[lambdaName] = lambdaObject;
    }
  }

  private createLambdaDefinitionSubstitutions(): { [key: string]: string } {
    const definitionSubstitutions: { [key: string]: string } = {};

    let lambdaName: keyof typeof this.lambdaObjects;
    for (lambdaName in this.lambdaObjects) {
      const lambdaObject = this.lambdaObjects[lambdaName];
      const sfnSubtitutionKey = `__${this.camelCaseToSnakeCase(lambdaObject.name)}_lambda_function_arn__`;
      definitionSubstitutions[sfnSubtitutionKey] =
        lambdaObject.lambdaFunction.currentVersion.functionArn;
    }

    return definitionSubstitutions;
  }

  private createLambdaApiFunction(props: LambdaApiFunctionProps) {
    const lambdaApiFunction = new PythonUvFunction(this, 'DataSharingApi', {
      entry: path.join(__dirname, '../interface'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      environment: {
        /* DynamoDB env vars */
        DYNAMODB_HOST: `https://dynamodb.${this.region}.amazonaws.com`,
        DYNAMODB_PACKAGING_JOB_TABLE_NAME: props.packagingDynamoDbApiTable.tableName,
        DYNAMODB_PUSH_JOB_TABLE_NAME: props.pushJobDynamoDbApiTable.tableName,
        /* SSM and Secrets Manager env vars */
        HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        DATA_SHARING_BASE_URL: `https://${props.customDomainNamePrefix}.${props.hostnameSsmParameterObj.stringValue}`,
        /* Event bridge env vars */
        EVENT_BUS_NAME: props.eventBus.eventBusName,
        EVENT_SOURCE: props.eventSource,
        /* Event detail types */
        EVENT_DETAIL_TYPE_CREATE_PACKAGE_JOB: props.eventDetailTypes.packageEvents.createJob,
        EVENT_DETAIL_TYPE_UPDATE_PACKAGE_JOB: props.eventDetailTypes.packageEvents.updateJob,
        EVENT_DETAIL_TYPE_CREATE_PUSH_JOB: props.eventDetailTypes.pushEvents.createJob,
        EVENT_DETAIL_TYPE_UPDATE_PUSH_JOB: props.eventDetailTypes.pushEvents.updateJob,
        /* SFN env vars */
        PACKAGE_JOB_STATE_MACHINE_ARN: props.packagingStateMachine.stateMachineArn,
        PRESIGN_STATE_MACHINE_ARN: props.presigningStateMachine.stateMachineArn,
        PUSH_JOB_STATE_MACHINE_ARN: props.pushStateMachine.stateMachineArn,
        /* Package bucket */
        PACKAGE_BUCKET_NAME: props.packagingLookUpBucket.bucketName,
      },
      layers: [props.dataSharingLayer, props.fileManagerLayer],
      bundling: {
        buildArgs: {
          TARGETPLATFORM: lambda.Architecture.ARM_64.dockerPlatform,
        },
      },
    });

    // Give lambda function permissions to put events on the event bus
    props.eventBus.grantPutEventsTo(lambdaApiFunction.currentVersion);

    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(lambdaApiFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(lambdaApiFunction.currentVersion);

    // Give lambda execution permissions to the three sfns
    props.packagingStateMachine.grantStartExecution(lambdaApiFunction.currentVersion);
    props.presigningStateMachine.grantStartSyncExecution(lambdaApiFunction.currentVersion);
    props.pushStateMachine.grantStartExecution(lambdaApiFunction.currentVersion);

    // Allow read/write access to the dynamodb table
    props.packagingDynamoDbApiTable.grantReadWriteData(lambdaApiFunction.currentVersion);
    props.pushJobDynamoDbApiTable.grantReadWriteData(lambdaApiFunction.currentVersion);

    // Lambda needs read access to the packaging bucket in order to generate the presigned urls
    // FIXME: Filemanager should be doing this instead
    props.packagingLookUpBucket.grantRead(
      lambdaApiFunction.currentVersion,
      `${props.packagingLookUpPrefix}*`
    );

    // Grant query permissions on indexes
    const packaging_index_arn_list: string[] = props.packagingDynamoDbTableIndexNames.map(
      (index_name) => {
        return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.packagingDynamoDbApiTable.tableName}/index/${index_name}-index`;
      }
    );
    const push_index_arn_list: string[] = props.pushJobDynamoDbTableIndexNames.map((index_name) => {
      return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.pushJobDynamoDbApiTable.tableName}/index/${index_name}-index`;
    });

    lambdaApiFunction.currentVersion.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: [...packaging_index_arn_list, ...push_index_arn_list],
      })
    );

    NagSuppressions.addResourceSuppressions(
      lambdaApiFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Need access to packaging look up bucket',
        },
      ],
      true
    );

    return lambdaApiFunction;
  }

  // Add the http routes to the API Gateway
  private add_http_routes(apiGateway: ApiGatewayConstruct, apiIntegration: HttpLambdaIntegration) {
    // Routes for API schemas
    new HttpRoute(this, 'GetSchemaHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: new HttpNoneAuthorizer(), // No auth needed for schema
      routeKey: HttpRouteKey.with(`/schema/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.POST),
    });
    new HttpRoute(this, 'PatchHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.PATCH),
    });
    new HttpRoute(this, 'DeleteHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.DELETE),
    });
  }
}
