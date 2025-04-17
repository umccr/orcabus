import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { IStateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { IEventBus } from 'aws-cdk-lib/aws-events';

export interface EventTrigger {
  eventDetailType: string;
  eventSource?: string;
}

export interface FastqSyncEventTriggers {
  fastqSetUpdated: EventTrigger;
  fastqListRowUpdated: EventTrigger;
  fastqUnarchiving: EventTrigger;
  fastqSync: EventTrigger;
}

export interface LambdaBuildInputs {
  /* Python layers */
  fastqToolsLayer: PythonLayerVersion;
  fastqUnarchivingToolsLayer: PythonLayerVersion;
  fastqSyncToolsLayer: PythonLayerVersion;
  /* SSM and Secrets */
  hostnameSsmParameterObj: IStringParameter;
  orcabusTokenSecretObj: ISecret;
  /* S3 Stuff */
  pipelineCacheBucketName: string;
  pipelineCachePrefix: string;
}

export interface Lambdas {
  checkFastqSetIdAgainstRequirementsLambdaFunction: lambda.Function;
  getFastqListRowAndRequirementsLambdaFunction: lambda.Function;
  getFastqListRowIdsFromFastqSetIdLambdaFunction: lambda.Function;
  getFastqSetIdsFromFastqListRowIdsLambdaFunction: lambda.Function;
  launchRequirementJobLambdaFunction: lambda.Function;
}

export interface LaunchFastqListRowRequirementsSfnProps {
  getFastqListRowAndRequirementsLambdaFunction: lambda.Function;
  launchRequirementJobLambdaFunctionArn: lambda.Function;
}

export interface InitialiseTaskTokenForFastqSyncSfnProps {
  fastqSyncDynamoDbTable: ITableV2;
  checkFastqSetIdAgainstRequirementsLambdaFunction: lambda.Function;
  getFastqListRowFromFastqSetIdLambdaFunction: lambda.Function;
  launchRequirementsSfn: IStateMachine;
}

export interface FastqSetIdUpdatedSfnProps {
  fastqSyncDynamoDbTable: ITableV2;
  checkFastqSetIdAgainstRequirementsLambdaFunction: lambda.Function;
  getFastqListRowFromFastqSetIdLambdaFunction: lambda.Function;
  launchRequirementsSfn: IStateMachine;
}

export interface FastqListRowIdUpdatedSfnProps {
  getFastqSetIdsFromFastqListRowIdsLambdaFunction: lambda.Function;
  fastqSetIdUpdatedSfn: IStateMachine;
}

export interface FastqListRowIdUpdatedEventBridgeRuleProps {
  fastqListRowIdUpdatedSfn: IStateMachine;
  eventBus: IEventBus;
  eventTriggers: EventTrigger;
}

export interface FastqSetIdUpdatedEventBridgeRuleProps {
  fastqSetIdUpdatedSfn: IStateMachine;
  eventBus: IEventBus;
  eventTriggers: EventTrigger;
}

export interface FastqUnarchivingCompleteEventBridgeRuleProps {
  fastqListRowIdUpdatedSfn: IStateMachine;
  eventBus: IEventBus;
  eventTriggers: EventTrigger;
}

export interface FastqSyncEventBridgeRuleProps {
  taskTokenInitialiserSfn: IStateMachine;
  eventBus: IEventBus;
  eventTriggers: EventTrigger;
}

export interface FastqSyncManagerStackConfig {
  /*
  Orcabus token and zone name for external lambda functions
  */
  orcabusTokenSecretsManagerPath: string;
  hostedZoneNameSsmParameterPath: string;

  /*
  Data tables
  */
  fastqSyncDynamodbTableName: string;

  /*
  Event bus stuff
  */
  eventBusName: string;
  eventTriggers: FastqSyncEventTriggers;

  /*
  S3 Stuff
  */
  pipelineCacheBucketName: string;
  pipelineCachePrefix: string;
}
