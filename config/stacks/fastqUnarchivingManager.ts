import {
  AppStage,
  /* API Gateway */
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
  /* Secrets and ssms */
  jwtSecretName,
  hostedZoneNameParameterPath,
  /* DyanmoDB */
  fastqUnarchivingJobTableName,
  fastqUnarchivingJobTableIndexes,
  /* S3 */
  icav2PipelineCacheBucket,
  icav2PipelineCachePrefix,
  s3CopyStepsBucket,
  s3CopyStepsFunctionArn,
  /* Events */
  eventBusName,
  fastqUnarchivingEventDetailType,
  fastqUnarchivingManagerEventSource,
} from '../constants';

import { FastqUnarchivingManagerTableConfig } from '../../lib/workload/stateful/stacks/fastq-unarchiving-dynamodb/deploy';

import { FastqUnarchivingManagerStackConfig } from '../../lib/workload/stateless/stacks/fastq-unarchiving/deploy/interfaces';

// Stateful
export const getFastqUnarchivingManagerTableStackProps = (): FastqUnarchivingManagerTableConfig => {
  return {
    /* DynamoDB table for fastq list rows */
    fastqUnarchivingJobDynamodbTableName: fastqUnarchivingJobTableName,
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
      customDomainNamePrefix: 'fastq-unarchiving',
    },

    /*
    Events stuff
    */
    eventBusName: eventBusName,
    eventDetailType: fastqUnarchivingEventDetailType,
    eventSource: fastqUnarchivingManagerEventSource,

    /*
    Orcabus token and zone name for external lambda functions
    */
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,

    /*
    Data tables
    */
    fastqUnarchivingJobsDynamodbTableName: fastqUnarchivingJobTableName,
    /* Indexes - need permissions to query indexes */
    fastqUnarchivingJobsDynamodbIndexes: fastqUnarchivingJobTableIndexes,

    /*
    Buckets stuff
    */
    s3Byob: {
      bucketName: icav2PipelineCacheBucket[stage],
      prefix: `${icav2PipelineCachePrefix[stage]}restored/14d/`,
    },
    s3StepsCopy: {
      s3StepsCopyBucketName: s3CopyStepsBucket[stage],
      s3StepsCopyPrefix: 'FASTQ_UNARCHIVING/',
      s3StepsFunctionArn: s3CopyStepsFunctionArn[stage],
    },
  };
};
