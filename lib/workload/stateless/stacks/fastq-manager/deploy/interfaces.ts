import { ApiGatewayConstructProps } from '../../../../components/api-gateway';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface EventDetailTypeProps {
  updateFastqListRow: string;
  updateFastqSet: string;
}

export interface FastqManagerStackConfig {
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
  fastqListRowDynamodbTableName: string;
  fastqSetDynamodbTableName: string;
  fastqJobsDynamodbTableName: string;
  /* Indexes - need permissions to query indexes */
  fastqListRowDynamodbIndexes: string[];
  fastqSetDynamodbIndexes: string[];
  fastqJobsDynamodbIndexes: string[];

  /*
  Buckets stuff
  */
  pipelineCacheBucketName: string;
  pipelineCachePrefix: string;
  fastqManagerCacheBucketName: string;
  ntsmBucketName: string;

  /*
  Event bus stuff
  */
  eventBusName: string;
  eventSource: string;
  eventDetailType: EventDetailTypeProps;
}

export interface LambdaApiFunctionProps {
  /* Lambda layers */
  fileManagerLayer: PythonLayerVersion;
  metadataLayer: PythonLayerVersion;
  /* Tables */
  fastqListRowDynamodbTable: ITableV2;
  fastqSetDynamodbTable: ITableV2;
  fastqJobDynamodbTable: ITableV2;
  /* Table indexes */
  fastqListRowDynamodbIndexes: string[];
  fastqSetDynamodbIndexes: string[];
  fastqJobsDynamodbIndexes: string[];
  /* SSM and Secrets Manager */
  hostnameSsmParameterObj: IStringParameter;
  orcabusTokenSecretObj: ISecret;
  /* Events */
  eventBus: IEventBus;
  eventSource: string;
  eventDetailType: EventDetailTypeProps;
  /* SFN */
  qcStatsSfn: IStateMachine;
  ntsmCountSfn: IStateMachine;
  ntsmEvalXSfn: IStateMachine;
  ntsmEvalXYSfn: IStateMachine;
  fileCompressionSfn: IStateMachine;
}

export interface BuildSfnWithEcsProps {
  /* Buckets */
  pipelineCacheBucket: s3.IBucket;
  pipelineCachePrefix: string;
  resultsBucket: s3.IBucket;
  resultsPrefix: string;
  /* ECS */
  securityGroup: ec2.ISecurityGroup;
  /* Shared lambdas */
  getFastqObjectAndS3ObjectsLambdaFunction: lambda.Function;
  updateFastqObjectLambdaFunction: lambda.Function;
  updateJobObjectLambdaFunction: lambda.Function;
}

export interface BuildSfnNtsmEvalProps {
  /* Buckets - buckets to read from */
  ntsmBucket: s3.IBucket;
  ntsmPrefix: string;
  /* Lambdas */
  getFastqListRowObjectsInFastqSetLambdaFunction: lambda.Function;
  ntsmEvalLambdaFunction: lambda.Function;
  verifyRelatednessLambdaFunction: lambda.Function;
}

export interface sharedLambdaProps {
  hostnameSsmParameterObj: ssm.IStringParameter;
  orcabusTokenSecretObj: secretsmanager.ISecret;
  fastqToolsLayer: PythonLayerVersion;
  fastqJobDynamodbTable: dynamodb.ITable;
}

export interface sharedLambdaOutputs {
  getFastqObjectAndS3ObjectsLambdaFunction: lambda.Function;
  updateFastqObjectLambdaFunction: lambda.Function;
  updateJobObjectLambdaFunction: lambda.Function;
}

export interface ntsmEvalLambdaProps {
  hostnameSsmParameterObj: ssm.IStringParameter;
  orcabusTokenSecretObj: secretsmanager.ISecret;
  fastqToolsLayer: PythonLayerVersion;
  ntsmBucket: s3.IBucket;
}

export interface ntsmEvalLambdaOutputs {
  getFastqListRowObjectsInFastqSetLambdaFunction: lambda.Function;
  ntsmEvalLambdaFunction: lambda.Function;
  verifyRelatednessLambdaFunction: lambda.Function;
}
