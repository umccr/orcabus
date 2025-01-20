import {
  AppStage,
  fastqManagerTableName,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
  jwtSecretName,
  hostedZoneNameParameterPath,
} from '../constants';
import { FastqManagerTableConfig } from '../../lib/workload/stateful/stacks/fastq-manager-db/deploy/stack';
import { FastqManagerStackConfig } from '../../lib/workload/stateless/stacks/fastq-manager/deploy/stack';

// Stateful
export const getFastqManagerTableStackProps = (): FastqManagerTableConfig => {
  return {
    dynamodbTableName: fastqManagerTableName,
  };
};

// Stateless
export const getFastqManagerStackProps = (stage: AppStage): FastqManagerStackConfig => {
  return {
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'FastqManager',
      customDomainNamePrefix: 'fastq',
    },
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,
  };
};
