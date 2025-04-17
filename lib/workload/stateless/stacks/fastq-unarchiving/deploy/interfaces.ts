import { ApiGatewayConstructProps } from '../../../../components/api-gateway';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { IBucket } from 'aws-cdk-lib/aws-s3';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface EventDetailTypeProps {
  createJob: string;
  updateJob: string;
}

export interface S3StepsCopyProps {
  s3StepsCopyBucketName: string;
  s3StepsFunctionArn: string;
  s3StepsCopyPrefix: string;
}

export interface S3ByobProps {
  bucketName: string;
  prefix: string;
}

export interface FastqUnarchivingManagerStackConfig {
  /*
  API Gateway props
  */
  apiGatewayCognitoProps: ApiGatewayConstructProps;

  /*
  Orcabus token and zone name for external lambda functions
  */
  orcabusTokenSecretsManagerPath: string;
  hostedZoneNameSsmParameterPath: string;

  /*
  Data tables
  */
  fastqUnarchivingJobsDynamodbTableName: string;
  /* Indexes - need permissions to query indexes */
  fastqUnarchivingJobsDynamodbIndexes: string[];

  /*
  S3 Steps Copy stuff
  */
  s3StepsCopy: S3StepsCopyProps;
  s3Byob: S3ByobProps;

  /*
  Event bus stuff
  */
  eventBusName: string;
  eventSource: string;
  eventDetailType: EventDetailTypeProps;
}

export interface LambdaApiFunctionProps {
  /* Tables */
  fastqUnarchivingJobDynamodbTable: ITableV2;
  /* Table indexes */
  fastqUnarchivingJobsDynamodbIndexes: string[];
  /* SSM and Secrets Manager */
  hostnameSsmParameterObj: IStringParameter;
  orcabusTokenSecretObj: ISecret;
  /* Events */
  eventBus: IEventBus;
  eventSource: string;
  eventDetailType: EventDetailTypeProps;
  /* State machines */
  fastqUnarchivingStateMachine: IStateMachine;
}

export interface sharedLambdaProps {
  hostnameSsmParameterObj: ssm.IStringParameter;
  orcabusTokenSecretObj: secretsmanager.ISecret;
  fastqUnarchivingManagerToolsLayer: PythonLayerVersion;
  fastqManagerToolsLayer: PythonLayerVersion;
  fileManagerToolsLayer: PythonLayerVersion;
}

export interface sharedLambdaFunctionObjects {
  createCsvForS3StepsCopyLambdaFunction: lambda.Function;
  findOriginalIngestIdLambdaFunction: lambda.Function;
  splitFastqIdsByInstrumentRunIdLambdaFunction: lambda.Function;
  updateIngestIdLambdaFunction: lambda.Function;
  updateJobDatabaseLambdaFunction: lambda.Function;
}

export interface runUnarchivingSfnProps {
  /* Lambda functions to use */
  lambdas: sharedLambdaFunctionObjects;
  /* S3 Steps Copy */
  s3StepsCopy: S3StepsCopyProps;
  s3Byob: S3ByobProps;
}
