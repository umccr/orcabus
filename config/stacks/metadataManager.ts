import {
  AppStage,
  cognitoApiGatewayProps,
  computeSecurityGroupName,
  corsAllowOrigins,
  vpcProps,
} from '../constants';
import { MetadataManagerStackProps } from '../../lib/workload/stateless/stacks/metadata-manager/deploy/stack';
import { RemovalPolicy } from 'aws-cdk-lib';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';

export const getMetadataManagerStackProps = (stage: AppStage): MetadataManagerStackProps => {
  const logsConfig = {
    retention: stage === AppStage.PROD ? RetentionDays.TWO_YEARS : RetentionDays.TWO_WEEKS,
    removalPolicy: stage === AppStage.PROD ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
  };

  const isDailySync = stage == AppStage.PROD ? true : false;

  return {
    vpcProps,
    isDailySync: isDailySync,
    lambdaSecurityGroupName: computeSecurityGroupName,
    apiGatewayCognitoProps: { ...cognitoApiGatewayProps, apiGwLogsConfig: logsConfig },
    corsAllowOrigins,
  };
};
