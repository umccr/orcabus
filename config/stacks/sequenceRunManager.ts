import {
  AppStage,
  basespaceAccessTokenSecretName,
  cognitoApiGatewayConfig,
  computeSecurityGroupName,
  corsAllowOrigins,
  eventBusName,
  logsApiGatewayConfig,
  vpcProps,
} from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/stack';

export const getSequenceRunManagerStackProps = (stage: AppStage): SequenceRunManagerStackProps => {
  const getSlackTopicName = (stage: AppStage) => {
    if (stage === AppStage.BETA) {
      return 'AwsChatBotTopic-alerts'; // 'alerts-dev' channel binding topic
    }
    if (stage === AppStage.GAMMA) {
      return 'AwsChatBotTopic-alerts'; // 'alerts-stg' channel binding topic
    }
    return 'AwsChatBotTopic'; // 'biobots' channel binding topic -- https://github.com/umccr/orcabus/issues/875
  };

  const getOrcabusUIBaseUrl = (stage: AppStage) => {
    if (stage === AppStage.BETA) {
      return 'https://orcaui.dev.umccr.org';
    }
    if (stage === AppStage.GAMMA) {
      return 'https://orcaui.stg.umccr.org';
    }
    return 'https://orcaui.umccr.org';
  };

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
    slackTopicName: getSlackTopicName(stage),
    orcabusUIBaseUrl: getOrcabusUIBaseUrl(stage),
  };
};
