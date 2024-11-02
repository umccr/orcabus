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

export interface OraDecompressionConstructProps {
  sfnPrefix: string;
  icav2AccessTokenSecretId: string;
}

export class OraDecompressionConstruct extends Construct {
  public readonly sfnObject: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: OraDecompressionConstructProps) {
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
    const oraDecompressionImage = new ecrAssets.DockerImageAsset(this, 'OraDecompression', {
      directory: path.join(__dirname, 'tasks', 'ora_decompression'),
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
    const oraDecompressionContainer = taskDefinition.addContainer('oraDecompressionContainer', {
      image: ecs.ContainerImage.fromDockerImageAsset(oraDecompressionImage),
      containerName: `${props.sfnPrefix}-orad-container`,
      logging: ecs.LogDriver.awsLogs({
        streamPrefix: 'orad',
        logRetention: RetentionDays.ONE_WEEK,
      }),
    });

    // Set up step function
    // Build state machine object
    this.sfnObject = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: `${props.sfnPrefix}-ora-decompression-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/decompress_ora_fastq_pair_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* ICAv2 Secret ID */
        __icav2_access_token_secret_id__: icav2SecretObj.secretName,
        /* Task Definition and Cluster ARNs */
        __ora_decompression_cluster_arn__: cluster.clusterArn,
        __ora_task_definition_arn__: taskDefinition.taskDefinitionArn,
        __ora_container_name__: oraDecompressionContainer.containerName,
        __subnets__: cluster.vpc.privateSubnets.map((subnet) => subnet.subnetId).join(','),
        __sg_group__: securityGroup.securityGroupId,
      },
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
