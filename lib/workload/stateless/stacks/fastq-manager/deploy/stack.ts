import path from 'path';
import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as fs from 'fs';
import { vpcProps as mainVpcProps } from '../../../../../../config/constants';

// Importing AWS CloudWatch Logs related modules
import * as awsLogs from 'aws-cdk-lib/aws-logs';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';

// Importing AWS Lambda related modules
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';
import { PythonUvFunction } from '../../../../components/uv-python-lambda-image-builder';
import { FilemanagerToolsPythonLambdaLayer } from '../../../../components/python-filemanager-tools-layer';
import { MetadataToolsPythonLambdaLayer } from '../../../../components/python-metadata-tools-layer';
import { FastqToolsPythonLambdaLayer } from '../../../../components/python-fastq-tools-layer';

// Importing AWS DynamoDB related modules
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

// Importing AWS IAM related modules
import * as iam from 'aws-cdk-lib/aws-iam';

// Importing AWS API Gateway related modules
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  HttpMethod,
  HttpNoneAuthorizer,
  HttpRoute,
  HttpRouteKey,
} from 'aws-cdk-lib/aws-apigatewayv2';
import { ApiGatewayConstruct } from '../../../../components/api-gateway';

// Importing AWS SSM and Secrets Manager related modules
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

// Importing AWS EventBridge related modules
import * as events from 'aws-cdk-lib/aws-events';

// Importing AWS S3 related modules
import * as s3 from 'aws-cdk-lib/aws-s3';

// Importing AWS Step Functions related modules
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { IStateMachine, LogLevel } from 'aws-cdk-lib/aws-stepfunctions';

// Importing AWS ECS related modules
import * as ecs from 'aws-cdk-lib/aws-ecs';
import { ContainerInsights, FargateTaskDefinition } from 'aws-cdk-lib/aws-ecs';
import * as ecrAssets from 'aws-cdk-lib/aws-ecr-assets';

// Importing AWS EC2 related modules
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { IVpc } from 'aws-cdk-lib/aws-ec2';

// Importing CDK Nag related modules
import { NagSuppressions } from 'cdk-nag';

// Importing interfaces
import {
  BuildSfnNtsmEvalProps,
  BuildSfnWithEcsProps,
  FastqManagerStackConfig,
  LambdaApiFunctionProps,
  ntsmEvalLambdaOutputs,
  ntsmEvalLambdaProps,
  sharedLambdaOutputs,
  sharedLambdaProps,
} from './interfaces';
import { ManagedPolicy } from 'aws-cdk-lib/aws-iam';

export type FastqManagerStackProps = FastqManagerStackConfig & cdk.StackProps;

export class FastqManagerStack extends Stack {
  public readonly API_VERSION = 'v1';
  public readonly FASTQ_URI_PREFIX = 'fastq';
  public readonly FASTQ_CACHE_PREFIX = 'cache/';
  public readonly NTSM_BUCKET_PREFIX = 'ntsm/';
  private mainVpc: IVpc;

  constructor(scope: Construct, id: string, props: StackProps & FastqManagerStackProps) {
    super(scope, id, props);

    /* Set tables */
    const fastqListRowDynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'fastq_list_row_dynamodb_table',
      props.fastqListRowDynamodbTableName
    );
    const fastqSetDynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'fastq_set_dynamodb_table',
      props.fastqSetDynamodbTableName
    );
    const fastqJobDynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'jobs_dynamodb_table',
      props.fastqJobsDynamodbTableName
    );

    /* Get buckets */
    const pipelineCacheBucket = s3.Bucket.fromBucketName(
      this,
      'pipeline_bucket',
      props.pipelineCacheBucketName
    );
    const fastqManagerCacheBucket = s3.Bucket.fromBucketName(
      this,
      'fastq_bucket',
      props.fastqManagerCacheBucketName
    );
    const ntsmBucket = s3.Bucket.fromBucketName(this, 'ntsm_bucket', props.ntsmBucketName);

    /* Get event bus */
    const eventBus = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Set the main vpc object
    this.set_main_vpc();

    // Create the FileManager Tool Layer
    const fileManagerLayer = new FilemanagerToolsPythonLambdaLayer(
      this,
      'filemanager-tools-layer',
      {
        layerPrefix: 'fqm',
      }
    );

    // Create the Metadata tool layer
    const metadataLayer = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'fqm',
    });

    // Create the fastq tools layer
    const fastqToolsLayer = new FastqToolsPythonLambdaLayer(this, 'fastq-tools-layer', {
      layerPrefix: 'fqm',
    });

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

    // Create the shared lambdas used in various step functions
    const sharedLambdas = this.build_shared_lambda_functions_in_sfns({
      /* Tables */
      fastqJobDynamodbTable: fastqJobDynamodbTable,
      /* Fastq Tools */
      fastqToolsLayer: fastqToolsLayer.lambdaLayerVersionObj,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
    });

    const ntsmLambdas = this.build_ntsm_evaluation_lambda_functions({
      /* Fastq Tools */
      fastqToolsLayer: fastqToolsLayer.lambdaLayerVersionObj,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
      ntsmBucket: ntsmBucket,
    });

    // Build the step functions
    const qcStatsSfn = this.build_qc_stats_sfn({
      /* Buckets */
      pipelineCacheBucket: pipelineCacheBucket,
      pipelineCachePrefix: props.pipelineCachePrefix,
      resultsBucket: fastqManagerCacheBucket,
      resultsPrefix: this.FASTQ_CACHE_PREFIX,
      /* Shared lambdas */
      updateFastqObjectLambdaFunction: sharedLambdas.updateFastqObjectLambdaFunction,
      updateJobObjectLambdaFunction: sharedLambdas.updateJobObjectLambdaFunction,
      getFastqObjectAndS3ObjectsLambdaFunction:
        sharedLambdas.getFastqObjectAndS3ObjectsLambdaFunction,
      /* Security */
      securityGroup: this.generate_security_group('qc-sg'),
    });

    const fileCompressionSfn = this.build_file_compression_sfn({
      /* Buckets */
      pipelineCacheBucket: pipelineCacheBucket,
      pipelineCachePrefix: props.pipelineCachePrefix,
      resultsBucket: fastqManagerCacheBucket,
      resultsPrefix: this.FASTQ_CACHE_PREFIX,
      /* Shared lambdas */
      updateFastqObjectLambdaFunction: sharedLambdas.updateFastqObjectLambdaFunction,
      updateJobObjectLambdaFunction: sharedLambdas.updateJobObjectLambdaFunction,
      getFastqObjectAndS3ObjectsLambdaFunction:
        sharedLambdas.getFastqObjectAndS3ObjectsLambdaFunction,
      /* Security */
      securityGroup: this.generate_security_group('file-compression-info-sg'),
    });

    const ntsmCountSfn = this.build_ntsm_count_sfn({
      /* Buckets */
      pipelineCacheBucket: pipelineCacheBucket,
      pipelineCachePrefix: props.pipelineCachePrefix,
      resultsBucket: ntsmBucket,
      resultsPrefix: this.NTSM_BUCKET_PREFIX,
      /* Shared lambdas */
      updateFastqObjectLambdaFunction: sharedLambdas.updateFastqObjectLambdaFunction,
      updateJobObjectLambdaFunction: sharedLambdas.updateJobObjectLambdaFunction,
      getFastqObjectAndS3ObjectsLambdaFunction:
        sharedLambdas.getFastqObjectAndS3ObjectsLambdaFunction,
      /* Security */
      securityGroup: this.generate_security_group('ntsm-sg'),
    });

    const ntsmEvalXSfn = this.build_ntsm_eval_x_sfn({
      /* Buckets */
      ntsmBucket: ntsmBucket,
      ntsmPrefix: this.NTSM_BUCKET_PREFIX,
      /* Lambdas */
      getFastqListRowObjectsInFastqSetLambdaFunction:
        ntsmLambdas.getFastqListRowObjectsInFastqSetLambdaFunction,
      ntsmEvalLambdaFunction: ntsmLambdas.ntsmEvalLambdaFunction,
      verifyRelatednessLambdaFunction: ntsmLambdas.verifyRelatednessLambdaFunction,
    });

    const ntsmEvalXYSfn = this.build_ntsm_eval_x_y_sfn({
      /* Buckets */
      ntsmBucket: ntsmBucket,
      ntsmPrefix: this.NTSM_BUCKET_PREFIX,
      /* Lambdas */
      getFastqListRowObjectsInFastqSetLambdaFunction:
        ntsmLambdas.getFastqListRowObjectsInFastqSetLambdaFunction,
      ntsmEvalLambdaFunction: ntsmLambdas.ntsmEvalLambdaFunction,
      verifyRelatednessLambdaFunction: ntsmLambdas.verifyRelatednessLambdaFunction,
    });

    // Api handler function
    const lambdaFunction = this.build_api_lambda_function({
      /* Lambda layers */
      fileManagerLayer: fileManagerLayer.lambdaLayerVersionObj,
      metadataLayer: metadataLayer.lambdaLayerVersionObj,
      /* Tables */
      fastqListRowDynamodbTable: fastqListRowDynamodbTable,
      fastqSetDynamodbTable: fastqSetDynamodbTable,
      fastqJobDynamodbTable: fastqJobDynamodbTable,
      /* Table indexes */
      fastqListRowDynamodbIndexes: props.fastqListRowDynamodbIndexes,
      fastqSetDynamodbIndexes: props.fastqSetDynamodbIndexes,
      fastqJobsDynamodbIndexes: props.fastqJobsDynamodbIndexes,
      /* SSM and Secrets Manager */
      hostnameSsmParameterObj: hostnameSsmParameterObj,
      orcabusTokenSecretObj: orcabusTokenSecretObj,
      /* Events */
      eventBus: eventBus,
      eventSource: props.eventSource,
      eventDetailType: props.eventDetailType,
      /* SFN */
      qcStatsSfn: qcStatsSfn,
      ntsmCountSfn: ntsmCountSfn,
      ntsmEvalXSfn: ntsmEvalXSfn,
      ntsmEvalXYSfn: ntsmEvalXYSfn,
      fileCompressionSfn: fileCompressionSfn,
    });

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', lambdaFunction);

    // Routes for API schemas
    this.add_http_routes(apiGateway, apiIntegration);
  }

  private set_main_vpc() {
    this.mainVpc = ec2.Vpc.fromLookup(this, 'MainVpc', mainVpcProps);
  }

  private generate_security_group(securityGroupName: string): ec2.ISecurityGroup {
    return new ec2.SecurityGroup(this, securityGroupName, {
      vpc: this.mainVpc,
      securityGroupName: securityGroupName,
    });
  }

  private generate_ecs_cluster(clusterId: string): ecs.Cluster {
    return new ecs.Cluster(this, clusterId, {
      clusterName: clusterId,
      vpc: this.mainVpc,
      enableFargateCapacityProviders: true,
      containerInsightsV2: ContainerInsights.ENABLED,
    });
  }

  private build_ecs_task_definition(
    vCpu: number,
    memoryLimitGiB: number,
    taskName: string
  ): FargateTaskDefinition {
    /*
    256 (.25 vCPU) - Available memory values: 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB)

    512 (.5 vCPU) - Available memory values: 1024 (1 GB), 2048 (2 GB), 3072 (3 GB), 4096 (4 GB)

    1024 (1 vCPU) - Available memory values: 2048 (2 GB), 3072 (3 GB), 4096 (4 GB), 5120 (5 GB), 6144 (6 GB), 7168 (7 GB), 8192 (8 GB)

    2048 (2 vCPU) - Available memory values: Between 4096 (4 GB) and 16384 (16 GB) in increments of 1024 (1 GB)

    4096 (4 vCPU) - Available memory values: Between 8192 (8 GB) and 30720 (30 GB) in increments of 1024 (1 GB)

    8192 (8 vCPU) - Available memory values: Between 16384 (16 GB) and 61440 (60 GB) in increments of 4096 (4 GB)

    16384 (16 vCPU) - Available memory values: Between 32768 (32 GB) and 122880 (120 GB) in increments of 8192 (8 GB)
    */
    const taskDefinition = new ecs.FargateTaskDefinition(this, taskName, {
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
      // Multiple cpu by 2^10 to get the value in CPU units
      cpu: vCpu * 1024,
      // Multiple memory by 2^20 to get the value in MiB
      memoryLimitMiB: memoryLimitGiB * 1024,
    });

    // Allow the task definition role ecr access to the guardduty agent
    // Which is in another account - 005257825471.dkr.ecr.ap-southeast-2.amazonaws.com/aws-guardduty-agent-fargate
    // https://docs.aws.amazon.com/guardduty/latest/ug/prereq-runtime-monitoring-ecs-support.html#before-enable-runtime-monitoring-ecs
    taskDefinition.taskRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy')
    );

    return taskDefinition;
  }

  private build_shared_lambda_functions_in_sfns(props: sharedLambdaProps): sharedLambdaOutputs {
    const getFastqObjectAndS3ObjectsLambdaFunction = new PythonUvFunction(
      this,
      'getFastqObjectAndS3ObjectsLambdaFunction',
      {
        entry: path.join(__dirname, '../app/shared/lambdas/get_fastq_object_with_s3_objs_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_fastq_object_with_s3_objs.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(getFastqObjectAndS3ObjectsLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(
      getFastqObjectAndS3ObjectsLambdaFunction.currentVersion
    );

    const updateFastqObjectLambdaFunction = new PythonUvFunction(
      this,
      'updateFastqObjectLambdaFunction',
      {
        entry: path.join(__dirname, '../app/shared/lambdas/update_fastq_object_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'update_fastq_object.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
        layers: [props.fastqToolsLayer],
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(updateFastqObjectLambdaFunction.currentVersion);
    props.hostnameSsmParameterObj.grantRead(updateFastqObjectLambdaFunction.currentVersion);

    const updateJobObjectLambdaFunction = new PythonUvFunction(
      this,
      'updateJobObjectLambdaFunction',
      {
        entry: path.join(__dirname, '../app/shared/lambdas/update_job_object_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'update_job_object.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        environment: {
          JOB_TABLE_NAME: props.fastqJobDynamodbTable.tableName,
        },
      }
    );

    // Give lambda function read/write access to job table
    props.fastqJobDynamodbTable.grantReadWriteData(updateJobObjectLambdaFunction.currentVersion);

    return {
      getFastqObjectAndS3ObjectsLambdaFunction: getFastqObjectAndS3ObjectsLambdaFunction,
      updateFastqObjectLambdaFunction: updateFastqObjectLambdaFunction,
      updateJobObjectLambdaFunction: updateJobObjectLambdaFunction,
    };
  }

  private build_ntsm_evaluation_lambda_functions(
    props: ntsmEvalLambdaProps
  ): ntsmEvalLambdaOutputs {
    const getFastqListRowObjectsInFastqSetLambdaFunction = new PythonUvFunction(
      this,
      'getFastqListRowObjectsInFastqSetLambdaFunction',
      {
        entry: path.join(
          __dirname,
          '../app/ntsm/lambdas/get_fastq_list_row_objects_in_fastq_set_py'
        ),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_fastq_list_row_objects_in_fastq_set.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
        layers: [props.fastqToolsLayer],
        environment: {
          /* SSM and Secrets Manager env vars */
          HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
          ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        },
      }
    );
    // Give lambda function permissions to secrets and ssm parameters
    props.orcabusTokenSecretObj.grantRead(
      getFastqListRowObjectsInFastqSetLambdaFunction.currentVersion
    );
    props.hostnameSsmParameterObj.grantRead(
      getFastqListRowObjectsInFastqSetLambdaFunction.currentVersion
    );

    const ntsmEvalLambdaFunction = new DockerImageFunction(this, 'ntsmEvalLambdaFunction', {
      code: DockerImageCode.fromImageAsset(path.join(__dirname, '../app/ntsm/lambdas/ntsm_eval')),
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.seconds(60),
      memorySize: 2048,
    });
    // ntsm bucket will need permissions to download files from the ntsm bucket
    props.ntsmBucket.grantRead(ntsmEvalLambdaFunction.currentVersion);

    // CDK Nag Suppression
    NagSuppressions.addResourceSuppressions(
      ntsmEvalLambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'grantRead uses an asterisk to allow access to all objects in the bucket',
        },
      ],
      true
    );

    const verifyRelatednessLambdaFunction = new PythonUvFunction(
      this,
      'verifyRelatednessLambdaFunction',
      {
        entry: path.join(__dirname, '../app/ntsm/lambdas/check_relatedness_list_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'check_relatedness_list.py',
        handler: 'handler',
        timeout: Duration.seconds(60),
        memorySize: 2048,
      }
    );

    return {
      getFastqListRowObjectsInFastqSetLambdaFunction:
        getFastqListRowObjectsInFastqSetLambdaFunction,
      ntsmEvalLambdaFunction: ntsmEvalLambdaFunction,
      verifyRelatednessLambdaFunction: verifyRelatednessLambdaFunction,
    };
  }

  private read_ora_dockerfile_contents(dockerfilePath: string): string {
    return fs.readFileSync(dockerfilePath, 'utf-8');
  }

  private prepend_docker_image_with_ora_image(
    dockerfilePath: string,
    dockerfileOutputPath: string
  ) {
    const oraContentsPath = path.join(__dirname, '../app/shared/ecr/ubuntu_with_ora/Dockerfile');
    const oraDockerContents = this.read_ora_dockerfile_contents(oraContentsPath);

    const dockerContents = this.read_ora_dockerfile_contents(dockerfilePath);

    // Write the new docker contents back to the original
    fs.writeFileSync(
      dockerfileOutputPath,
      dockerContents.replace('__ORA_IMAGE_HEADER__', oraDockerContents)
    );
  }

  private build_qc_stats_sfn(props: BuildSfnWithEcsProps): IStateMachine {
    /* Attributes */
    const architecture = lambda.Architecture.ARM_64;

    // Get Dockerfile contents from ../app/shared/ecr/ubuntu_with_ora/Dockerfile
    const qcEcrDir = path.join(__dirname, '../app/qc/tasks/get_sequali_stats');
    const qcEcrDockerFile = path.join(qcEcrDir, 'Dockerfile');
    const qcEcrDockerOutFile = path.join(qcEcrDir, 'Dockerfile.out');

    // Prepend the Dockerfile with the ORA image
    this.prepend_docker_image_with_ora_image(qcEcrDockerFile, qcEcrDockerOutFile);

    // Build the qcDockerImageAsset from this new file
    const qcDockerImageAsset = new ecrAssets.DockerImageAsset(this, 'qcEcr', {
      directory: qcEcrDir,
      buildArgs: {
        TARGETPLATFORM: architecture.dockerPlatform,
        // qcEcrDockerOutFile relative to qcEcrDir
      },
      file: path.relative(qcEcrDir, qcEcrDockerOutFile),
    });

    // Set up the cluster and task definitions
    const cluster = this.generate_ecs_cluster('qc-cluster');
    const taskDefinition = this.build_ecs_task_definition(2, 4, 'qc-task');
    const qcContainer = taskDefinition.addContainer('qc-container', {
      image: ecs.ContainerImage.fromDockerImageAsset(qcDockerImageAsset),
      containerName: 'qc-container',
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'qc-logs',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Allow task definition access to read/write from buckets
    props.pipelineCacheBucket.grantRead(taskDefinition.taskRole, `${props.pipelineCachePrefix}*`);
    props.resultsBucket.grantReadWrite(taskDefinition.taskRole, `${props.resultsPrefix}*`);

    // Set up the step function
    const qcStateMachine = new sfn.StateMachine(this, 'qcStateMachine', {
      stateMachineName: `fastq-manager-qc-stats-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/qc/step_functions_templates/run_sequali_stats_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* S3 stuff */
        __fastq_manager_cache_bucket__: props.resultsBucket.bucketName,
        __fastq_manager_cache_prefix__: props.resultsPrefix,
        /* Cluster stuff */
        __sequali_cluster_arn__: cluster.clusterArn,
        __sequali_task_definition_arn__: taskDefinition.taskDefinitionArn,
        __sequali_qc_container_name__: qcContainer.containerName,
        /* VPC stuff */
        __subnets__: cluster.vpc.privateSubnets.map((subnet) => subnet.subnetId).join(','),
        __security_group__: props.securityGroup.securityGroupId,
        /* Lambdas */
        __get_fastq_object_with_s3_objs_lambda_function_arn__:
          props.getFastqObjectAndS3ObjectsLambdaFunction.currentVersion.functionArn,
        __update_fastq_object_lambda_function_arn__:
          props.updateFastqObjectLambdaFunction.currentVersion.functionArn,
        __update_job_object_lambda_function_arn__:
          props.updateJobObjectLambdaFunction.currentVersion.functionArn,
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqObjectAndS3ObjectsLambdaFunction,
      props.updateFastqObjectLambdaFunction,
      props.updateJobObjectLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(qcStateMachine);
    });

    // Give the state machine permissions to read/write to the fastq manager bucket
    // Task writes to cache bucket and we need to retrieve the results in a later step
    props.resultsBucket.grantRead(qcStateMachine, `${props.resultsPrefix}*`);

    NagSuppressions.addResourceSuppressions(
      qcStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'qcstatemachine will need to read from the fastq manager bucket',
        },
      ],
      true
    );

    // Give the state machine permissions to run tasks on the cluster
    taskDefinition.grantRun(qcStateMachine);

    // {
    //   "Action": "ecr:GetAuthorizationToken",
    //   "Effect": "Allow",
    //   "Resource": "*"
    // },
    NagSuppressions.addResourceSuppressions(
      taskDefinition,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Fargate has GetAuthorizationToken permission on all resources by default',
        },
      ],
      true
    );

    /* Grant the state machine access to monitor the tasks */
    qcStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    return qcStateMachine;
  }

  private build_file_compression_sfn(props: BuildSfnWithEcsProps): IStateMachine {
    /* Attributes */
    const architecture = lambda.Architecture.ARM_64;

    // Get Dockerfile contents from ../app/shared/ecr/ubuntu_with_ora/Dockerfile
    const gzipEcrDir = path.join(
      __dirname,
      '../app/file_compression_info/tasks/get_gzip_filesize_in_bytes'
    );
    const gzipEcrDockerFile = path.join(gzipEcrDir, 'Dockerfile');
    const gzipEcrDockerOutFile = path.join(gzipEcrDir, 'Dockerfile.out');

    // Prepend the Dockerfile with the ORA image
    this.prepend_docker_image_with_ora_image(gzipEcrDockerFile, gzipEcrDockerOutFile);

    // Build the gzip Docker image asset from this new file
    const gzipEcrImageAsset = new ecrAssets.DockerImageAsset(this, 'gzipEcr', {
      directory: gzipEcrDir,
      buildArgs: {
        TARGETPLATFORM: architecture.dockerPlatform,
      },
      file: path.relative(gzipEcrDir, gzipEcrDockerOutFile),
    });

    // Get Dockerfile contents from ../app/shared/ecr/ubuntu_with_ora/Dockerfile
    const rawMd5sumEcrDir = path.join(
      __dirname,
      '../app/file_compression_info/tasks/get_raw_md5sum'
    );
    const rawMd5sumEcrDockerFile = path.join(rawMd5sumEcrDir, 'Dockerfile');
    const rawMd5sumEcrDockerOutFile = path.join(rawMd5sumEcrDir, 'Dockerfile.out');

    // Prepend the Dockerfile with the ORA image
    this.prepend_docker_image_with_ora_image(rawMd5sumEcrDockerFile, rawMd5sumEcrDockerOutFile);

    // Build the rawMd5sum Docker image asset from this new file
    const rawMd5sumEcrImageAsset = new ecrAssets.DockerImageAsset(this, 'rawMd5sumEcr', {
      directory: rawMd5sumEcrDir,
      buildArgs: {
        TARGETPLATFORM: architecture.dockerPlatform,
      },
      file: path.relative(rawMd5sumEcrDir, rawMd5sumEcrDockerOutFile),
    });

    // Set up the cluster and task definitions
    // We should be able to share the same task definition for both gzip and raw md5sum tasks
    const gzipCluster = this.generate_ecs_cluster('gzip-file-compression-cluster');
    const rawMd5sumCluster = this.generate_ecs_cluster('raw-md5sum-file-compression-cluster');
    const gzipTaskDefinition = this.build_ecs_task_definition(
      4,
      8,
      'gzipfilesizeinbytes-compression-task'
    );
    const rawMd5sumTaskDefinition = this.build_ecs_task_definition(
      4,
      8,
      'rawmd5sum-compression-task'
    );

    // Generate separate containers for each service
    const gzipContainer = gzipTaskDefinition.addContainer('gzip-container', {
      image: ecs.ContainerImage.fromDockerImageAsset(gzipEcrImageAsset),
      containerName: 'gzip-container',
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'gzip-logs',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });
    const md5sumContainer = rawMd5sumTaskDefinition.addContainer('md5sum-container', {
      image: ecs.ContainerImage.fromDockerImageAsset(rawMd5sumEcrImageAsset),
      containerName: 'md5sum-container',
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'md5sum-logs',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Allow task definition access to read/write from buckets
    // Both gzip and md5sum tasks will need to read from the pipeline cache bucket
    // and write to the fastq cache bucket
    props.pipelineCacheBucket.grantRead(
      gzipTaskDefinition.taskRole,
      `${props.pipelineCachePrefix}*`
    );
    props.pipelineCacheBucket.grantRead(
      rawMd5sumTaskDefinition.taskRole,
      `${props.pipelineCachePrefix}*`
    );
    props.resultsBucket.grantReadWrite(gzipTaskDefinition.taskRole, `${props.resultsPrefix}*`);
    props.resultsBucket.grantReadWrite(rawMd5sumTaskDefinition.taskRole, `${props.resultsPrefix}*`);

    // Set up the step function
    const fileCompressionStateMachine = new sfn.StateMachine(this, 'gzipStateMachine', {
      stateMachineName: `fastq-manager-gzip-stats-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/file_compression_info/step_functions_templates/update_file_metadata_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* S3 stuff */
        __fastq_manager_cache_bucket__: props.resultsBucket.bucketName,
        __fastq_manager_cache_prefix__: props.resultsPrefix,
        /* Cluster stuff */
        __gzip_file_compression_cluster_arn__: gzipCluster.clusterArn,
        __gzip_file_compression_task_definition_arn__: gzipTaskDefinition.taskDefinitionArn,
        __gzip_file_size_in_bytes_container_name__: gzipContainer.containerName,
        __md5sum_file_compression_cluster_arn__: rawMd5sumCluster.clusterArn,
        __md5sum_file_compression_task_definition_arn__: rawMd5sumTaskDefinition.taskDefinitionArn,
        __raw_md5sum_container_name__: md5sumContainer.containerName,
        /* VPC stuff */
        __gzip_subnets__: gzipCluster.vpc.privateSubnets.map((subnet) => subnet.subnetId).join(','),
        __md5sum_subnets__: rawMd5sumCluster.vpc.privateSubnets
          .map((subnet) => subnet.subnetId)
          .join(','),
        __security_group__: props.securityGroup.securityGroupId,
        /* Lambdas */
        __get_fastq_object_with_s3_objs_lambda_function_arn__:
          props.getFastqObjectAndS3ObjectsLambdaFunction.currentVersion.functionArn,
        __update_fastq_object_lambda_function_arn__:
          props.updateFastqObjectLambdaFunction.currentVersion.functionArn,
        __update_job_object_lambda_function_arn__:
          props.updateJobObjectLambdaFunction.currentVersion.functionArn,
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqObjectAndS3ObjectsLambdaFunction,
      props.updateFastqObjectLambdaFunction,
      props.updateJobObjectLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(fileCompressionStateMachine);
    });

    // Give the state machine permissions to read/write to the fastq manager bucket
    // Task writes to cache bucket and we need to retrieve the results in a later step
    props.resultsBucket.grantRead(fileCompressionStateMachine, `${props.resultsPrefix}*`);

    // Give the state machine permissions to run tasks on the cluster
    gzipTaskDefinition.grantRun(fileCompressionStateMachine);
    rawMd5sumTaskDefinition.grantRun(fileCompressionStateMachine);

    // {
    //   "Action": "ecr:GetAuthorizationToken",
    //   "Effect": "Allow",
    //   "Resource": "*"
    // },
    NagSuppressions.addResourceSuppressions(
      gzipTaskDefinition,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Fargate has GetAuthorizationToken permission on all resources by default',
        },
      ],
      true
    );
    NagSuppressions.addResourceSuppressions(
      rawMd5sumTaskDefinition,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Fargate has GetAuthorizationToken permission on all resources by default',
        },
      ],
      true
    );
    NagSuppressions.addResourceSuppressions(
      fileCompressionStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'We need to collect files from the fastq manager bucket and so we obviously need a wildcard',
        },
      ],
      true
    );

    /* Grant the state machine access to monitor the tasks */
    fileCompressionStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    return fileCompressionStateMachine;
  }

  private build_ntsm_count_sfn(props: BuildSfnWithEcsProps): IStateMachine {
    /* Attributes */
    const architecture = lambda.Architecture.ARM_64;

    // Get Dockerfile contents from ../app/shared/ecr/ubuntu_with_ora/Dockerfile
    const ntsmCountEcrDir = path.join(__dirname, '../app/ntsm/tasks/ntsm_count');
    const ntsmCountEcrDockerFile = path.join(ntsmCountEcrDir, 'Dockerfile');
    const ntsmCountEcrDockerOutFile = path.join(ntsmCountEcrDir, 'Dockerfile.out');

    // Prepend the Dockerfile with the ORA image
    this.prepend_docker_image_with_ora_image(ntsmCountEcrDockerFile, ntsmCountEcrDockerOutFile);

    // Build the ntsmCount Docker image asset from this new file
    const ntsmCountEcrImageAsset = new ecrAssets.DockerImageAsset(this, 'ntsmCountEcr', {
      directory: ntsmCountEcrDir,
      buildArgs: {
        TARGETPLATFORM: architecture.dockerPlatform,
      },
      file: path.relative(ntsmCountEcrDir, ntsmCountEcrDockerOutFile),
    });

    // Set up the cluster and task definitions
    const cluster = this.generate_ecs_cluster('ntsm-cluster');
    const taskDefinition = this.build_ecs_task_definition(4, 8, 'ntsm-task');
    const ntsmCount = taskDefinition.addContainer('ntsm-container', {
      image: ecs.ContainerImage.fromDockerImageAsset(ntsmCountEcrImageAsset),
      containerName: 'ntsm-container',
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'ntsm-logs',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Allow task definition access to read/write from buckets
    props.pipelineCacheBucket.grantRead(taskDefinition.taskRole, `${props.pipelineCachePrefix}*`);
    props.resultsBucket.grantReadWrite(taskDefinition.taskRole, `${props.resultsPrefix}*`);

    // Set up the step function
    const ntsmStateMachine = new sfn.StateMachine(this, 'ntsmCountStateMachine', {
      stateMachineName: `fastq-manager-ntsm-count-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/ntsm/step_functions_templates/run_ntsm_count_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* S3 stuff */
        __ntsm_bucket__: props.resultsBucket.bucketName,
        __ntsm_prefix__: props.resultsPrefix,
        /* Cluster stuff */
        __ntsm_count_cluster_arn__: cluster.clusterArn,
        __ntsm_count_task_definition_arn__: taskDefinition.taskDefinitionArn,
        __ntsm_count_container_name__: ntsmCount.containerName,
        /* VPC stuff */
        __subnets__: cluster.vpc.privateSubnets.map((subnet) => subnet.subnetId).join(','),
        __security_group__: props.securityGroup.securityGroupId,
        /* Lambdas */
        __get_fastq_object_with_s3_objs_lambda_function_arn__:
          props.getFastqObjectAndS3ObjectsLambdaFunction.currentVersion.functionArn,
        __update_fastq_object_lambda_function_arn__:
          props.updateFastqObjectLambdaFunction.currentVersion.functionArn,
        __update_job_object_lambda_function_arn__:
          props.updateJobObjectLambdaFunction.currentVersion.functionArn,
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqObjectAndS3ObjectsLambdaFunction,
      props.updateFastqObjectLambdaFunction,
      props.updateJobObjectLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(ntsmStateMachine);
    });

    // Give the state machine permissions to read/write to the fastq manager bucket
    // Task writes to cache bucket and we need to retrieve the results in a later step
    props.resultsBucket.grantRead(ntsmStateMachine, `${props.resultsPrefix}*`);

    // Give the state machine permissions to run tasks on the cluster
    taskDefinition.grantRun(ntsmStateMachine);

    // {
    //   "Action": "ecr:GetAuthorizationToken",
    //   "Effect": "Allow",
    //   "Resource": "*"
    // },
    NagSuppressions.addResourceSuppressions(
      taskDefinition,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Fargate has GetAuthorizationToken permission on all resources by default',
        },
      ],
      true
    );

    NagSuppressions.addResourceSuppressions(
      ntsmStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Statemachine needs permissions to read from the bucket, so obviously we need a wildcard',
        },
      ],
      true
    );

    /* Grant the state machine access to monitor the tasks */
    ntsmStateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    return ntsmStateMachine;
  }

  private build_ntsm_eval_x_sfn(props: BuildSfnNtsmEvalProps): IStateMachine {
    // Set up the step function
    const ntsmEvalXStateMachine = new sfn.StateMachine(this, 'ntsmEvalXStateMachine', {
      stateMachineName: `fastq-manager-ntsm-eval-x-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/ntsm/step_functions_templates/run_ntsm_eval_x_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __get_fastq_objects_in_fastq_set_lambda_function_arn__:
          props.getFastqListRowObjectsInFastqSetLambdaFunction.currentVersion.functionArn,
        __ntsm_evaluation_lambda_function_arn__:
          props.ntsmEvalLambdaFunction.currentVersion.functionArn,
        __summarise_outputs_lambda_function_arn__:
          props.verifyRelatednessLambdaFunction.currentVersion.functionArn,
      },
      // The evaluation workflows are express workflows
      stateMachineType: sfn.StateMachineType.EXPRESS,
      // Enable logging on the state machine
      logs: {
        level: LogLevel.ALL,
        // Create a new log group for the state machine
        destination: new awsLogs.LogGroup(this, 'ntsmEvalXLogGroup', {
          retention: RetentionDays.ONE_DAY,
        }),
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqListRowObjectsInFastqSetLambdaFunction,
      props.ntsmEvalLambdaFunction,
      props.verifyRelatednessLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(ntsmEvalXStateMachine);
    });

    // Give the lambda function that performs the evaluation read/write access to the ntsm bucket
    // This is where the ntsm files are that we read in to compare
    props.ntsmBucket.grantRead(props.ntsmEvalLambdaFunction.currentVersion, `${props.ntsmPrefix}*`);

    NagSuppressions.addResourceSuppressions(
      ntsmEvalXStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Evaluation state machine needs permissions to read from the bucket, so obviously we need a wildcard',
        },
      ],
      true
    );

    return ntsmEvalXStateMachine;
  }

  private build_ntsm_eval_x_y_sfn(props: BuildSfnNtsmEvalProps): IStateMachine {
    // Set up the step function
    const ntsmEvalXYStateMachine = new sfn.StateMachine(this, 'ntsmEvalXYStateMachine', {
      stateMachineName: `fastq-manager-ntsm-eval-x-y-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          '../app/ntsm/step_functions_templates/run_ntsm_eval_x_y_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __get_fastq_objects_in_fastq_set_lambda_function_arn__:
          props.getFastqListRowObjectsInFastqSetLambdaFunction.currentVersion.functionArn,
        __ntsm_evaluation_lambda_function_arn__:
          props.ntsmEvalLambdaFunction.currentVersion.functionArn,
        __summarise_outputs_lambda_function_arn__:
          props.verifyRelatednessLambdaFunction.currentVersion.functionArn,
      },
      // The evaluation workflows are express workflows
      stateMachineType: sfn.StateMachineType.EXPRESS,
      // Enable logging on the state machine
      logs: {
        level: LogLevel.ALL,
        // Create a new log group for the state machine
        destination: new awsLogs.LogGroup(this, 'ntsmEvalXYLogGroup', {
          retention: RetentionDays.ONE_DAY,
        }),
      },
    });

    // Give the state machine permissions to invoke the lambdas
    [
      props.getFastqListRowObjectsInFastqSetLambdaFunction,
      props.ntsmEvalLambdaFunction,
      props.verifyRelatednessLambdaFunction,
    ].forEach((lambdaFunction) => {
      lambdaFunction.currentVersion.grantInvoke(ntsmEvalXYStateMachine);
    });

    // Give the lambda function that performs the evaluation read/write access to the ntsm bucket
    // This is where the ntsm files are that we read in to compare
    props.ntsmBucket.grantRead(props.ntsmEvalLambdaFunction.currentVersion, `${props.ntsmPrefix}*`);

    NagSuppressions.addResourceSuppressions(
      ntsmEvalXYStateMachine,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Evaluation state machine needs permissions to read from the bucket, so obviously we need a wildcard',
        },
      ],
      true
    );

    return ntsmEvalXYStateMachine;
  }

  private build_api_lambda_function(props: LambdaApiFunctionProps) {
    const lambdaApiFunction = new PythonUvFunction(this, 'FastqManagerApi', {
      entry: path.join(__dirname, '../app/api'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      environment: {
        /* DynamoDB env vars */
        DYNAMODB_HOST: `https://dynamodb.${this.region}.amazonaws.com`,
        DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME: props.fastqListRowDynamodbTable.tableName,
        DYNAMODB_FASTQ_SET_TABLE_NAME: props.fastqSetDynamodbTable.tableName,
        DYNAMODB_FASTQ_JOB_TABLE_NAME: props.fastqJobDynamodbTable.tableName,
        /* SSM and Secrets Manager env vars */
        HOSTNAME_SSM_PARAMETER: props.hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: props.orcabusTokenSecretObj.secretName,
        FASTQ_BASE_URL: `https://${this.FASTQ_URI_PREFIX}.${props.hostnameSsmParameterObj.stringValue}`,
        /* Event bridge env vars */
        EVENT_BUS_NAME: props.eventBus.eventBusName,
        EVENT_SOURCE: props.eventSource,
        /* Event detail types */
        EVENT_DETAIL_TYPE_FASTQ_LIST_ROW_STATE_CHANGE: props.eventDetailType.updateFastqListRow,
        EVENT_DETAIL_TYPE_FASTQ_SET_ROW_STATE_CHANGE: props.eventDetailType.updateFastqSet,
        /* SFN env vars */
        QC_STATS_AWS_STEP_FUNCTION_ARN: props.qcStatsSfn.stateMachineArn,
        NTSM_COUNT_AWS_STEP_FUNCTION_ARN: props.ntsmCountSfn.stateMachineArn,
        NTSM_EVAL_X_AWS_STEP_FUNCTION_ARN: props.ntsmEvalXSfn.stateMachineArn,
        NTSM_EVAL_X_Y_AWS_STEP_FUNCTION_ARN: props.ntsmEvalXYSfn.stateMachineArn,
        FILE_COMPRESSION_AWS_STEP_FUNCTION_ARN: props.fileCompressionSfn.stateMachineArn,
      },
      layers: [props.metadataLayer, props.fileManagerLayer],
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
    props.qcStatsSfn.grantStartExecution(lambdaApiFunction.currentVersion);
    props.ntsmCountSfn.grantStartExecution(lambdaApiFunction.currentVersion);
    props.fileCompressionSfn.grantStartExecution(lambdaApiFunction.currentVersion);

    // Give lambda execution permissions to the two 'express' sfns
    props.ntsmEvalXSfn.grantStartSyncExecution(lambdaApiFunction.currentVersion);
    props.ntsmEvalXYSfn.grantStartSyncExecution(lambdaApiFunction.currentVersion);

    // Allow read/write access to the dynamodb table
    props.fastqListRowDynamodbTable.grantReadWriteData(lambdaApiFunction.currentVersion);
    props.fastqSetDynamodbTable.grantReadWriteData(lambdaApiFunction.currentVersion);
    props.fastqJobDynamodbTable.grantReadWriteData(lambdaApiFunction.currentVersion);

    // Grant query permissions on indexes
    const fastq_list_row_index_arn_list: string[] = props.fastqListRowDynamodbIndexes.map(
      (index_name) => {
        return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.fastqListRowDynamodbTable.tableName}/index/${index_name}-index`;
      }
    );
    const fastq_set_index_arn_list: string[] = props.fastqSetDynamodbIndexes.map((index_name) => {
      return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.fastqSetDynamodbTable.tableName}/index/${index_name}-index`;
    });
    const fastq_jobs_index_arn_list: string[] = props.fastqJobsDynamodbIndexes.map((index_name) => {
      return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.fastqJobDynamodbTable.tableName}/index/${index_name}-index`;
    });
    lambdaApiFunction.currentVersion.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: [
          ...fastq_list_row_index_arn_list,
          ...fastq_set_index_arn_list,
          ...fastq_jobs_index_arn_list,
        ],
      })
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
