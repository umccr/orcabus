import { App, Aspects } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { StatelessPipelineStack } from '../../lib/pipeline/orcabus-stateless-pipeline-stack';
import * as config from '../../config/constants';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Stateless Stack
describe('cdk-nag-stateless-pipeline', () => {
  let stack: StatelessPipelineStack;
  let app: App;

  // The pipeline is not happy with the RustFunction for testing as it doesn't return
  // constructId when using toString() at the lambda. Will revisit this later but for now
  // it will ignore filemanager (current prod do not have filemanager config)

  // -- Remove below --
  const temp = config.getEnvironmentConfig('prod');
  jest.spyOn(config, 'getEnvironmentConfig').mockImplementation(() => temp);
  // -- --

  beforeEach(() => {
    app = new App({});
    stack = new StatelessPipelineStack(app, 'TestStack', {
      env: {
        account: '123456789',
        region: 'ap-southeast-2',
      },
    });
    Aspects.of(stack).add(new AwsSolutionsChecks());

    NagSuppressions.addStackSuppressions(stack, [
      { id: 'AwsSolutions-IAM4', reason: 'Allow CDK Pipeline' },
      { id: 'AwsSolutions-IAM5', reason: 'Allow CDK Pipeline' },
      { id: 'AwsSolutions-S1', reason: 'Allow CDK Pipeline' },
      { id: 'AwsSolutions-KMS5', reason: 'Allow CDK Pipeline' },
      { id: 'AwsSolutions-CB3', reason: 'Allow CDK Pipeline' },
    ]);
  });

  test('cdk-nag AwsSolutions Pack errors', () => {
    const errors = Annotations.fromStack(stack)
      .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(errors).toHaveLength(0);
  });

  test('cdk-nag AwsSolutions Pack warnings', () => {
    const warnings = Annotations.fromStack(stack)
      .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(warnings).toHaveLength(0);
  });
});
