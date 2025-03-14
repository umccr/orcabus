import {
  AppStage,
  fastqListRowTableName,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
  jwtSecretName,
  hostedZoneNameParameterPath,
  fastqListRowManagerIndexes,
  fastqSetTableName,
  fastqSetManagerIndexes,
  fastqJobTableName,
  fastqJobManagerIndexes,
  FastqUnarchivingManagerCacheBucket,
  ntsmBucket,
  FastqUnarchivingManagerEventSource,
  FastqUnarchivingManagerEventDetails,
  icav2PipelineCacheBucket,
  icav2PipelineCachePrefix,
  eventBusName,
} from '../constants';

// Stateful
export const getFastqUnarchivingManagerTableStackProps = (
  stage: AppStage
): FastqUnarchivingManagerTableConfig => {
  return {
    /* DynamoDB table for fastq list rows */
    fastqListRowDynamodbTableName: fastqListRowTableName,
    fastqSetDynamodbTableName: fastqSetTableName,
    fastqJobDynamodbTableName: fastqJobTableName,
    /* Buckets */
    FastqUnarchivingManagerCacheBucketName: FastqUnarchivingManagerCacheBucket[stage],
    ntsmBucketName: ntsmBucket[stage],
  };
};

// Stateless
export const getFastqUnarchivingManagerStackProps = (
  stage: AppStage
): FastqUnarchivingManagerStackConfig => {
  return {
    /*
    API Gateway props
    */
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'FastqUnarchivingManager',
      customDomainNamePrefix: 'fastq',
    },

    /*
    Orcabus token and zone name for external lambda functions
    */
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,

    /*
    Data tables
    */
    fastqListRowDynamodbTableName: fastqListRowTableName,
    fastqSetDynamodbTableName: fastqSetTableName,
    fastqJobsDynamodbTableName: fastqJobTableName,
    /* Indexes - need permissions to query indexes */
    fastqListRowDynamodbIndexes: fastqListRowManagerIndexes,
    fastqSetDynamodbIndexes: fastqSetManagerIndexes,
    fastqJobsDynamodbIndexes: fastqJobManagerIndexes,

    /*
    Buckets stuff
    */
    pipelineCacheBucketName: icav2PipelineCacheBucket[stage],
    pipelineCachePrefix: icav2PipelineCachePrefix[stage],
    FastqUnarchivingManagerCacheBucketName: FastqUnarchivingManagerCacheBucket[stage],
    ntsmBucketName: ntsmBucket[stage],

    /*
    Event bus stuff
    */
    eventBusName: eventBusName,
    eventSource: FastqUnarchivingManagerEventSource,
    eventDetailType: FastqUnarchivingManagerEventDetails,
  };
};
