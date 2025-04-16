import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  icav2DataCopyEventSource,
  icav2DataCopyManagerDynamodbTableName,
  icav2DataCopySyncDetailType,
} from '../constants';
import { Icav2DataCopyManagerTableConfig } from '../../lib/workload/stateful/stacks/icav2-data-copy-manager-dynamo-db/deploy';
import { Icav2DataCopyManagerConfig } from '../../lib/workload/stateless/stacks/icav2-data-copy-manager/deploy/interfaces';

/*
Internal constants
*/
const icav2DataCopyInternalDetailType = 'ICAv2DataCopyInternalSync';

// Stateful
export const getIcav2DataCopyManagerTableStackProps = (): Icav2DataCopyManagerTableConfig => {
  return {
    dynamodbTableName: icav2DataCopyManagerDynamodbTableName,
  };
};

// Stateless
export const getIcav2DataCopyManagerStackProps = (stage: AppStage): Icav2DataCopyManagerConfig => {
  return {
    /*
    Tables
    */
    dynamodbTableName: icav2DataCopyManagerDynamodbTableName,

    /*
    Event handling
    */
    eventBusName: eventBusName,
    icaEventPipeName: icaEventPipeStackName,
    eventSource: icav2DataCopyEventSource,
    eventExternalDetailType: icav2DataCopySyncDetailType,
    eventInternalDetailType: icav2DataCopyInternalDetailType,

    /*
    Names for things
    */
    stateMachinePrefix: 'icav2-data-copy',
    ruleNamePrefix: 'icav2-data-copy',

    /*
    Secrets
    */
    icav2AccessTokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  };
};
