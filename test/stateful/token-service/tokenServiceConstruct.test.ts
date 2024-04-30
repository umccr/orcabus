import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import { TokenServiceStack } from '../../../lib/workload/stateful/stacks/token-service/deploy/stack';
import { AppStage } from '../../../config/constants';

const constructConfig = getEnvironmentConfig(AppStage.BETA);
if (!constructConfig) throw new Error('No construct config for the test');

const mockApp = new cdk.App();

const stack = new TokenServiceStack(mockApp, 'TestTokenServiceStack', {
  env: {
    account: '123456789',
    region: 'ap-southeast-2',
  },
  ...constructConfig.stackProps.statefulConfig.tokenServiceStackProps,
});

beforeEach(() => {
  // pass
});

test('Test TokenService Creation', () => {
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::SecretsManager::Secret', {
    Name: 'orcabus/token-service-user',
  });
  template.hasResourceProperties('AWS::SecretsManager::Secret', {
    Name: 'orcabus/token-service-jwt',
  });
});
