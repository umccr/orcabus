import {
  AppStage,
  /* Events */
  eventBusName,
  fastqManagerEventDetails,
  fastqManagerEventSource,
  fastqSyncEventDetailType,
  fastqUnarchivingEventDetailType,
  fastqUnarchivingManagerEventSource,
  hostedZoneNameParameterPath,
  icav2PipelineCacheBucket,
  icav2PipelineCachePrefix,
  jwtSecretName,
} from '../constants';

import { FastqSyncManagerStackConfig } from '../../lib/workload/stateless/stacks/fastq-sync/deploy/interfaces';
import { FastqSyncTableConfig } from '../../lib/workload/stateful/stacks/fastq-sync-dynamodb/deploy/stack';

/*
export interface FastqSyncManagerStackConfig {
  /*
  Orcabus token and zone name for external lambda functions
  */
//orcabusTokenSecretsManagerPath: string;
//hostedZoneNameSsmParameterPath: string;

/*
  Data tables
  */
//fastqSyncDynamodbTableName: string;
/*
  Event bus stuff
  */
//eventBusName: string;
// eventTriggers: FastqSyncEventTriggers
//}
//*/

const fastqSyncDynamodbTableName = 'fastqSyncTokenTable';

// Stateful
export const getFastqSyncManagerTableStackProps = (): FastqSyncTableConfig => {
  return {
    /* DynamoDB table for fastq list rows */
    dynamodbTableName: fastqSyncDynamodbTableName,
  };
};

// Stateless
export const getFastqSyncManagerStackProps = (stage: AppStage): FastqSyncManagerStackConfig => {
  return {
    /*
    Table stuff
    */
    fastqSyncDynamodbTableName: fastqSyncDynamodbTableName,

    /*
    Events stuff
    */
    eventBusName: eventBusName,
    eventTriggers: {
      fastqSetUpdated: {
        eventSource: fastqManagerEventSource,
        eventDetailType: fastqManagerEventDetails.updateFastqSet,
      },
      fastqListRowUpdated: {
        eventSource: fastqManagerEventSource,
        eventDetailType: fastqManagerEventDetails.updateFastqListRow,
      },
      fastqUnarchiving: {
        eventSource: fastqUnarchivingManagerEventSource,
        eventDetailType: fastqUnarchivingEventDetailType.updateJob,
      },
      fastqSync: {
        eventDetailType: fastqSyncEventDetailType,
      },
    },

    /*
    Orcabus token and zone name for external lambda functions
    */
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,

    /*
    S3 Stuff
    */
    pipelineCacheBucketName: icav2PipelineCacheBucket[stage],
    pipelineCachePrefix: icav2PipelineCachePrefix[stage],
  };
};
