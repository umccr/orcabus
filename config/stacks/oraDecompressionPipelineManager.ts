import {
  AppStage,
  eventBusName,
  icav2AccessTokenSecretName,
  oraDecompressionIcav2ReadyEventSource,
  oraDecompressionIcav2EventSource,
  oraDecompressionIcav2EventDetailType,
  oraDecompressionStateMachinePrefix,
} from '../constants';
import { OraDecompressionPipelineManagerConfig } from '../../lib/workload/stateless/stacks/ora-decompression-manager/deploy';

// Stateless
export const getOraDecompressionManagerStackProps = (
  stage: AppStage
): OraDecompressionPipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    /* Internal and external buses */
    eventBusName: eventBusName,
    triggerEventSource: oraDecompressionIcav2ReadyEventSource,
    outputEventSource: oraDecompressionIcav2EventSource,
    /* Event handling */
    detailType: oraDecompressionIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: oraDecompressionStateMachinePrefix,
  };
};
