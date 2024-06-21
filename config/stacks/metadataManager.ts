import { AppStage, cognitoApiGatewayProps, computeSecurityGroupName, vpcProps } from '../constants';
import { MetadataManagerStackProps } from '../../lib/workload/stateless/stacks/metadata-manager/deploy/stack';

export const getMetadataManagerStackProps = (stage: AppStage): MetadataManagerStackProps => {
  const isDailySync = stage == AppStage.PROD ? true : false;

  return {
    vpcProps,
    isDailySync: isDailySync,
    lambdaSecurityGroupName: computeSecurityGroupName,
    apiGatewayCognitoProps: cognitoApiGatewayProps,
  };
};
