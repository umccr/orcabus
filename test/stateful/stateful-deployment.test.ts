import { App, Aspects } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { OrcaBusStatefulStack } from '../../lib/workload/orcabus-stateful-stack';
import { getEnvironmentConfig } from '../../config/constants';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}
// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig('prod')!;

describe('cdk-nag-stateful-stack', () => {
  let stack: OrcaBusStatefulStack;
  let app: App;

  beforeAll(() => {
    app = new App({ context: {} });
    stack = new OrcaBusStatefulStack(app, 'TestStack', {
      env: {
        account: '12345678',
        region: 'ap-southeast-2',
      },
      ...config.stackProps.orcaBusStatefulConfig,
    });
    Aspects.of(stack).add(new AwsSolutionsChecks());

    // Suppress CDK-NAG for secret rotation
    NagSuppressions.addResourceSuppressionsByPath(
      stack,
      `/${stack.stackName}/OrcaBusDatabaseConstruct/OrcaBusDatabaseConstructDbSecret/Resource`,
      [{ id: 'AwsSolutions-SMG4', reason: 'Dont require secret rotation' }]
    );
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
