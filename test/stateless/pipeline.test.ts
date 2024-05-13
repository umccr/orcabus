import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { StatelessPipelineStack } from '../../lib/pipeline/statelessPipelineStack';

// we are mocking the deployment stack here, as we have a dedicated cdk-nag test for deployment stack
// see the ./stateless-deployment.test.ts
jest.mock('../../lib/workload/stateless/statelessStackCollectionClass', () => {
  return {
    StatelessStackCollection: jest.fn().mockImplementation((value) => {
      return new Stack(value, 'mockStack', {});
    }),
  };
});

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Stateless Stack
describe('cdk-nag-stateless-pipeline', () => {
  const app: App = new App({});
  const stack: StatelessPipelineStack = new StatelessPipelineStack(app, 'TestStack', {
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

  NagSuppressions.addResourceSuppressionsByPath(stack, `/TestStack/GHRunnerCodeBuildProject`, [
    {
      id: 'AwsSolutions-CB4',
      reason: 'This codebuild does not use artifacts, so S3 KMS key is irrelevant.',
    },
  ]);

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
