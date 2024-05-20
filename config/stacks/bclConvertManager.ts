import { AppStage, vpcProps, eventBusName } from '../constants';
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
export const getBclConvertManagerStackProps = (): BclConvertManagerStackProps => {
  return {
    eventBusName,
    icav2EventTranslatorDynamodbTableName: dynamodbTableName,
    vpcProps: vpcProps,
    lambdaSecurityGroupName: 'OrcaBusIcaEventTranslatorSecurityGroup',
    schemasCodeBindingLambdaLayerArn:
      'SchemasCodeBindingLambdaLayerArn will be define in stateless stack collection.',
  };
};
