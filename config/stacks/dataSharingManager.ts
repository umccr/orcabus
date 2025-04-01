import {
  AppStage,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
  jwtSecretName,
  hostedZoneNameParameterPath,
  eventBusName,
  s3CopyStepsBucket,
  s3CopyStepsFunctionArn,
  icav2DataCopySyncDetailType,
  accountIdAlias,
  dataSharingPackageEventsDetailType,
  dataSharingPushEventsDetailType,
  fastqSyncEventDetailType,
  dataSharingEventsSource,
} from '../constants';
import { DataSharingS3AndTableConfig } from '../../lib/workload/stateful/stacks/data-sharing-s3-and-db/deploy/stack';
import { DataSharingStackConfig } from '../../lib/workload/stateless/stacks/data-sharing-manager/deploy/interfaces';

/* Internal constants */
const dataSharingCacheBucket: Record<AppStage, string> = {
  [AppStage.BETA]: `data-sharing-artifacts-${accountIdAlias.beta}-ap-southeast-2`,
  [AppStage.GAMMA]: `data-sharing-artifacts-${accountIdAlias.gamma}-ap-southeast-2`,
  [AppStage.PROD]: `data-sharing-artifacts-${accountIdAlias.prod}-ap-southeast-2`,
};
const dataSharingCachePrefix = 'packages/';
const packagingApiTableName = 'data-sharing-packaging-api-table';
const pushJobApiTableName = 'data-sharing-push-api-table';
const packagingLookUpTableName = 'data-sharing-packaging-lookup-table';
const packagingApiTableIndexes = ['package_name', 'status'];
const pushJobApiTableIndexes = ['package_id', 'package_name', 'status'];
const packagingLookUpTableIndexes = ['context', 'content'];

// Stateful
export const getDataSharingS3AndTableStackProps = (
  stage: AppStage
): DataSharingS3AndTableConfig => {
  return {
    /* DynamoDB table for apis */
    packagingApiTableName: packagingApiTableName,
    pushJobApiTableName: pushJobApiTableName,
    /* Cache dynamoDB table */
    packagingLookUpTableName: packagingLookUpTableName,
    /* Buckets */
    bucketName: dataSharingCacheBucket[stage],
    bucketPrefix: dataSharingCachePrefix,
  };
};

// Stateless
export const getDataSharingStackProps = (stage: AppStage): DataSharingStackConfig => {
  return {
    /*
    API Gateway props
    */
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'DataSharingManager',
      customDomainNamePrefix: 'data-sharing',
    },

    /*
    Orcabus token and zone name for external lambda functions
    */
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,

    /*
    API tables
    */
    packagingDynamoDbApiTableName: packagingApiTableName,
    pushJobDynamoDbApiTableName: pushJobApiTableName,
    /* Indexes - need permissions to query indexes */
    packagingDynamoDbApiTableIndexNames: packagingApiTableIndexes,
    pushJobDynamoDbTableIndexNames: pushJobApiTableIndexes,

    /*
    Cache tables
    */
    packagingLookUpDynamoDbTableName: packagingLookUpTableName,
    packagingLookUpDynamoDbTableIndexNames: packagingLookUpTableIndexes,

    /*
    s3StepsCopy Props
    */
    s3StepsCopyProps: {
      s3StepsCopyBucketName: s3CopyStepsBucket[stage],
      s3StepsCopyPrefix: 'DATA_SHARING/',
      s3StepsFunctionArn: s3CopyStepsFunctionArn[stage],
    },

    /*
    Bucket Stuff
    */
    packagingLookUpBucketName: dataSharingCacheBucket[stage],
    packagingSharingPrefix: dataSharingCachePrefix,

    /*
    Event bus stuff
    */
    eventBusName: eventBusName,
    eventSource: dataSharingEventsSource,
    eventDetailTypes: {
      packageEvents: {
        createJob: dataSharingPackageEventsDetailType.createPackageJob,
        updateJob: dataSharingPackageEventsDetailType.updatePackageJob,
      },
      pushEvents: {
        createJob: dataSharingPushEventsDetailType.createPushJob,
        updateJob: dataSharingPushEventsDetailType.updatePushJob,
      },
    },
    fastqSyncDetailType: fastqSyncEventDetailType,
    icav2JobCopyDetailType: icav2DataCopySyncDetailType,
  };
};
