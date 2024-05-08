import {
  IcaEventPipeStackProps,
  IcaEventTranslatorProps,
} from '../../lib/workload/stateful/stacks/ica-event-pipe/stack';
import { eventBusName, icaAwsAccountNumber, AppStage, vpcProps } from '../constants';
import { RemovalPolicy } from 'aws-cdk-lib';

export const getIcaEventPipeStackProps = (stage: AppStage): IcaEventPipeStackProps => {
  return {
    name: 'IcaEventPipeStack',
    eventBusName: eventBusName,
    slackTopicName: 'AwsChatBotTopic',
    icaAwsAccountNumber: icaAwsAccountNumber,
    IcaEventTranslatorProps: getIcaEventTranslatorProps(stage),
  };
};

export const getIcaEventTranslatorProps = (stage: AppStage): IcaEventTranslatorProps => {
  const basicIcaEventTranslatorProps = {
    icav2EventTranslatorDynamodbTableName: 'IcaEventTranslatorTable',
    vpcProps: vpcProps,
    lambdaSecurityGroupName: 'IcaEventTranslatorLambdaSecurityGroup',
  };
  switch (stage) {
    case AppStage.BETA:
      return {
        ...basicIcaEventTranslatorProps,
        removalPolicy: RemovalPolicy.DESTROY,
      };
      break;
    case AppStage.GAMMA:
      return {
        ...basicIcaEventTranslatorProps,
        removalPolicy: RemovalPolicy.DESTROY,
      };
      break;
    case AppStage.PROD:
      return {
        ...basicIcaEventTranslatorProps,
        removalPolicy: RemovalPolicy.RETAIN,
      };
      break;
    default:
      return {
        ...basicIcaEventTranslatorProps,
      };
  }
};
