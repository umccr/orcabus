import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { WorkflowManagerStackProps } from '../../lib/workload/stateless/stacks/workflow-manager/deploy/stack';
import {
  vpcProps,
  computeSecurityGroupName,
  eventBusName,
  cognitoUserPoolIdParameterName,
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
  AppStage,
} from '../constants';
import { RemovalPolicy } from 'aws-cdk-lib';

export const getWorkflowManagerStackProps = (stage: AppStage): WorkflowManagerStackProps => {
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
