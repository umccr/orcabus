import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  icav2DataCopyManagerDynamodbTableName,
} from '../constants';
import { Icav2DataCopyManagerTableConfig } from '../../lib/workload/stateful/stacks/icav2-data-copy-manager-dynamo-db/deploy';
import { Icav2DataCopyManagerConfig } from '../../lib/workload/stateless/stacks/icav2-data-copy-manager/deploy';

// Stateful
export const getIcav2DataCopyManagerTableStackProps = (): Icav2DataCopyManagerTableConfig => {
  return {
    dynamodbTableName: icav2DataCopyManagerDynamodbTableName,
  };
};

// Stateless
export const getIcav2DataCopyManagerStackProps = (stage: AppStage): Icav2DataCopyManagerConfig => {
  return {
    dynamodbTableName: icav2DataCopyManagerDynamodbTableName,
    eventBusName: eventBusName,
    icaEventPipeName: icaEventPipeStackName,
    stateMachinePrefix: 'icav2-data-copy-manager',
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  };
};
