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
  fastqManagerCacheBucket,
  ntsmBucket,
  fastqManagerEventSource,
  fastqManagerEventDetails,
  icav2PipelineCacheBucket,
  icav2PipelineCachePrefix,
  eventBusName,
} from '../constants';
import { FastqManagerTableConfig } from '../../lib/workload/stateful/stacks/fastq-manager-db/deploy/stack';
import { FastqManagerStackConfig } from '../../lib/workload/stateless/stacks/fastq-manager/deploy/interfaces';

// Stateful
export const getFastqManagerTableStackProps = (stage: AppStage): FastqManagerTableConfig => {
  return {
    /* DynamoDB table for fastq list rows */
    fastqListRowDynamodbTableName: fastqListRowTableName,
    fastqSetDynamodbTableName: fastqSetTableName,
    fastqJobDynamodbTableName: fastqJobTableName,
    /* Buckets */
    fastqManagerCacheBucketName: fastqManagerCacheBucket[stage],
    ntsmBucketName: ntsmBucket[stage],
  };
};

// Stateless
export const getFastqManagerStackProps = (stage: AppStage): FastqManagerStackConfig => {
  return {
    /*
    API Gateway props
    */
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'FastqManager',
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
    fastqManagerCacheBucketName: fastqManagerCacheBucket[stage],
    ntsmBucketName: ntsmBucket[stage],

    /*
    Event bus stuff
    */
    eventBusName: eventBusName,
    eventSource: fastqManagerEventSource,
    eventDetailType: fastqManagerEventDetails,
  };
};
