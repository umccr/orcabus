import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import {
  fileManagerPresignUserSecret,
  fileManagerPresignUser,
  AppStage,
} from '../../../config/constants';
import { AccessKeySecret } from '../../../lib/workload/stateful/stacks/access-key-secret';

const constructConfig = getEnvironmentConfig(AppStage.BETA)!;

const app = new cdk.App();

const stack = new AccessKeySecret(app, 'TestAccessKeySecret', {
  env: {
    account: '123456789',
    region: 'ap-southeast-2',
  },
  ...constructConfig.stackProps.statefulConfig.accessKeySecretStackProps,
});

describe('AccessKeySecret', () => {
  test('Test Construction', () => {
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Name: fileManagerPresignUserSecret,
    });
    template.hasResourceProperties('AWS::IAM::User', {
      UserName: fileManagerPresignUser,
    });
  });
});
