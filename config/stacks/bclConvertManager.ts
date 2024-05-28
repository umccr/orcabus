import { AppStage, vpcProps, eventBusName, icav2AccessTokenSecretName } from '../constants';
import { RemovalPolicy } from 'aws-cdk-lib';
import { BclConvertTableStackProps } from '../../lib/workload/stateful/stacks/bclconvert-dynamo-db/deploy/stack';
import { BclConvertManagerStackProps } from '../../lib/workload/stateless/stacks/bclconvert-manager/deploy/stack';

const dynamodbTableName = 'IcaEventTranslatorTable';

export const getBclConvertManagerTableStackProps = (stage: AppStage): BclConvertTableStackProps => {
  return {
    dynamodbTableName: dynamodbTableName,
    removalPolicy: stage === AppStage.PROD ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
  };
};
export const getBclConvertManagerStackProps = (stage: AppStage): BclConvertManagerStackProps => {
  return {
    eventBusName,
    icav2EventTranslatorDynamodbTableName: dynamodbTableName,
    vpcProps: vpcProps,
    lambdaSecurityGroupName: 'OrcaBusBclConvertManagerSecurityGroup',
    icav2JwtSecretsManagerPath: icav2AccessTokenSecretName[stage],
  };
};
