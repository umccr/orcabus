#!/usr/bin/env python3

import { Construct } from 'constructs';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as ecrAssets from 'aws-cdk-lib/aws-ecr-assets';
import { NagSuppressions } from 'cdk-nag';
import path from 'path';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';

export interface GzipRawMd5sumConstructProps {
  sfnPrefix: string;
  icav2AccessTokenSecretId: string;
}

export class GzipRawMd5sumDecompressionConstruct extends Construct {
  public readonly sfnObject: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: GzipRawMd5sumConstructProps) {
    super(scope, id);

    // Set up task definition and cluster
    // a fargate cluster we use for non-lambda Tasks
    // we sometimes need to execute tasks in a VPC context so we need one of these
    const vpc = ec2.Vpc.fromLookup(this, 'MainVpc', {
      vpcName: 'main-vpc',
    });
    const cluster = new ecs.Cluster(this, 'FargateCluster', {
      vpc: vpc,
      enableFargateCapacityProviders: true,
      containerInsights: true,
    });
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'FargateTaskDefinition', {
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.ARM64,
      },
      cpu: 8192, // Maps to 8 CPUs
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
    const gzipRawMd5sumImage = new ecrAssets.DockerImageAsset(this, 'gzipRawMd5sum', {
      directory: path.join(__dirname, 'tasks', 'gzip_to_raw_md5sum'),
      buildArgs: {
        TARGETPLATFORM: architecture.dockerPlatform,
      },
    });

    // Add permission to task role
    const icav2SecretObj = secretsManager.Secret.fromSecretNameV2(
      this,
      'icav2SecretObject',
      props.icav2AccessTokenSecretId
    );
    icav2SecretObj.grantRead(taskDefinition.taskRole);

    // Add container to task role
    const gzipToRawMd5sumContainer = taskDefinition.addContainer('gzipToRawMd5sumContainer', {
      image: ecs.ContainerImage.fromDockerImageAsset(gzipRawMd5sumImage),
      containerName: `${props.sfnPrefix}-container`,
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'gzipToRawMd5sum',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Build the lambdas
    const readIcav2FileContentsLambdaObj = new PythonFunction(this, 'read_icav2_file_contents_py', {
      entry: path.join(__dirname, 'lambdas', 'read_icav2_file_contents_py'),
      index: 'read_icav2_file_contents.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      memorySize: 1024, // Don't want pandas to kill the lambda
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2SecretObj.secretName,
      },
      timeout: Duration.seconds(300),
    });

    const deleteIcav2CacheUriLambdaObj = new PythonFunction(this, 'delete_icav2_cache_uri_py', {
      entry: path.join(__dirname, 'lambdas', 'delete_icav2_cache_uri_py'),
      index: 'delete_icav2_cache_uri.py',
      handler: 'handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      memorySize: 1024, // Don't want pandas to kill the lambda
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: icav2SecretObj.secretName,
      },
      timeout: Duration.seconds(300),
    });

    // Give the lambda permission to access the icav2 access token secret id
    [readIcav2FileContentsLambdaObj, deleteIcav2CacheUriLambdaObj].forEach((lambdaObj) => {
      icav2SecretObj.grantRead(lambdaObj.currentVersion);
    });

    // Set up step function
    // Build state machine object
    this.sfnObject = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: `${props.sfnPrefix}-gzip-to-raw-md5sum-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/get_raw_md5sum_for_fastq_gzip_pair_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* ICAv2 Secret ID */
        __icav2_access_token_secret_id__: icav2SecretObj.secretName,
        /* Task Definition and Cluster ARNs */
        __gzip_to_raw_md5sum_cluster_arn__: cluster.clusterArn,
        __gzip_to_raw_md5sum_task_definition_arn__: taskDefinition.taskDefinitionArn,
        __gzip_to_raw_md5sum_container_name__: gzipToRawMd5sumContainer.containerName,
        __subnets__: cluster.vpc.privateSubnets.map((subnet) => subnet.subnetId).join(','),
        __sg_group__: securityGroup.securityGroupId,
        /* Lambdas */
        __read_icav2_file_contents_lambda_function_arn__:
          readIcav2FileContentsLambdaObj.currentVersion.functionArn,
        __delete_icav2_cache_uri_lambda_function_arn__:
          deleteIcav2CacheUriLambdaObj.currentVersion.functionArn,
      },
    });

    // Allow the step function to invoke the lambda
    [readIcav2FileContentsLambdaObj, deleteIcav2CacheUriLambdaObj].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(this.sfnObject);
    });

    // Allow step function to run the ECS task
    taskDefinition.grantRun(this.sfnObject);

    // FIXME - cdk nag error on fargate task definition role
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
    this.sfnObject.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );
  }
}
