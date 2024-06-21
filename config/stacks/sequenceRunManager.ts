import {
  AppStage,
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
  cognitoUserPoolIdParameterName,
  computeSecurityGroupName,
  eventBusName,
  vpcProps,
} from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/stack';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { RemovalPolicy } from 'aws-cdk-lib';

export const getSequenceRunManagerStackProps = (stage: AppStage): SequenceRunManagerStackProps => {
  const logsConfig = {
    retention: stage === AppStage.PROD ? 14 : RetentionDays.TWO_YEARS,
    removalPolicy: stage === AppStage.PROD ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
  };

  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
    cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
    apiGwLogsConfig: logsConfig,
  };
};
