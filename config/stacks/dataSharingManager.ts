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
  dataSharingCacheBucket,
  dataSharingPackageEventsDetailType,
  dataSharingPushEventsDetailType,
  fastqSyncEventDetailType,
  dataSharingEventsSource,
  dataMartAthenaS3BucketName,
  dataMartAthenaS3Prefix,
  dataMartAthenaWorkgroup,
  dataMartAthenaDatabase,
  dataMartAthenaDataSource,
  dataMartAthenaLambdaFunctionName,
} from '../constants';
import { DataSharingS3AndTableConfig } from '../../lib/workload/stateful/stacks/data-sharing-s3-and-db/deploy/stack';
import { DataSharingStackConfig } from '../../lib/workload/stateless/stacks/data-sharing-manager/deploy/interfaces';

const dataSharingCachePrefix = 'packages/';
const pushLogsPrefix = 'push-logs/';
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
    pushLogsPrefix: pushLogsPrefix,

    // Athena stuff
    athenaProps: {
      athenaS3BucketName: dataMartAthenaS3BucketName[stage],
      athenaS3Prefix: dataMartAthenaS3Prefix,
      athenaWorkgroup: dataMartAthenaWorkgroup,
      athenaDatabase: dataMartAthenaDatabase,
      athenaDataSource: dataMartAthenaDataSource,
      athenaLambdaFunctionName: dataMartAthenaLambdaFunctionName,
    },

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
