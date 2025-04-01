// Various interfaces used in the project

import * as lambda from 'aws-cdk-lib/aws-lambda';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IEventBus } from 'aws-cdk-lib/aws-events';

export interface BuildLambdaProps {
  icav2AccessTokenSecretObj: ISecret;
}

export interface Lambdas {
  findSinglePartFilesLambdaFunction: lambda.Function;
  generateCopyJobListLambdaFunction: lambda.Function;
  launchIcav2CopyLambdaFunction: lambda.Function;
  uploadSinglePartFileLambdaFunction: lambda.Function;
}

export interface HandleCopyJobsSfnProps {
  /* Naming formation */
  stateMachinePrefix: string;

  /* Lambdas */
  findSinglePartFilesLambdaFunction: lambda.Function;
  generateCopyJobListLambdaFunction: lambda.Function;
  launchIcav2CopyLambdaFunction: lambda.Function;
  uploadSinglePartFileLambdaFunction: lambda.Function;

  /* Event Stuff */
  eventBus: IEventBus;
  icav2CopyServiceEventSource: string;
  icav2CopyServiceInternalDetailType: string;
  icav2CopyServiceExternalDetailType: string;
}

export interface Icav2DataCopyManagerConfig {
  /*
  Tables
  */
  dynamodbTableName: string;

  /*
  Event handling
  */
  eventBusName: string;
  icaEventPipeName: string;
  eventSource: string;
  eventInternalDetailType: string;
  eventExternalDetailType: string;

  /*
  Names for things
  */
  stateMachinePrefix: string;
  ruleNamePrefix: string;

  /*
  Secrets
  */
  icav2AccessTokenSecretId: string; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
}
