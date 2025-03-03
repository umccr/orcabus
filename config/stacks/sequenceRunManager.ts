import {
  region,
  AppStage,
  basespaceAccessTokenSecretName,
  cognitoApiGatewayConfig,
  computeSecurityGroupName,
  corsAllowOrigins,
  eventBusName,
  logsApiGatewayConfig,
  vpcProps,
  slackTopicName,
  accountIdAlias,
} from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/stack';

export const getSequenceRunManagerStackProps = (stage: AppStage): SequenceRunManagerStackProps => {
  const slackTopicArn =
    'arn:aws:sns:' + region + ':' + accountIdAlias[stage] + ':' + slackTopicName;
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'SequenceRunManager',
      customDomainNamePrefix: 'sequence',
    },
    bsshTokenSecretName: basespaceAccessTokenSecretName,
    slackTopicArn: slackTopicArn,
  };
};
