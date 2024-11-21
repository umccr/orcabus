import { WebSocketApiStackProps } from '../../lib/workload/stateless/stacks/client-websocket-conn/deploy';
import { AppStage, vpcProps, region, cognitoUserPoolIdParameterName } from '../constants';

export const getWebSocketApiStackProps = (stage: AppStage): WebSocketApiStackProps => {
  return {
    connectionTableName: 'OrcaBusClientWebsocketApiConnectionTable',
    websocketApigatewayName: `OrcaBusClientWebsocketApi${stage}`,
    lambdaSecurityGroupName: 'OrcaBusClientWebsocketApiSecurityGroup',
    vpcProps: vpcProps,
    websocketApiEndpointParameterName: `/orcabus/client-websocket-api-endpoint`,
    websocketStageName: stage,
    cognitoRegion: region,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
  };
};
