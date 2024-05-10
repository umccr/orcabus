import { AppStage, vpcProps, eventBusName } from '../constants';
import { RemovalPolicy } from 'aws-cdk-lib';
import { Icav2EventTranslatorTableStackProps } from '../../lib/workload/stateful/stacks/icav2-event-translator-dynamo-db/deploy/stack';
import { Icav2EventTranslatorStackProps } from '../../lib/workload/stateless/stacks/icav2-event-translator/deploy/stack';

export const getIcav2EventTranslatorTableStackProps = (
  stage: AppStage
): Icav2EventTranslatorTableStackProps => {
  return {
    dynamodbTableName: 'IcaEventTranslatorTable',
    removalPolicy: stage === AppStage.PROD ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
  };
};
export const getIcav2EventTranslatorStackProps = (): Icav2EventTranslatorStackProps => {
  return {
    eventBusName,
    icav2EventTranslatorDynamodbTableName: 'IcaEventTranslatorTable',
    vpcProps: vpcProps,
    lambdaSecurityGroupName: 'IcaEventTranslatorLambdaSecurityGroup',
  };
};
