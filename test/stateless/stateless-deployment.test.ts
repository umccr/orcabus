import { App, Aspects } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks } from 'cdk-nag';
import { OrcaBusStatelessStack } from '../../lib/workload/orcabus-stateless-stack';
import { getEnvironmentConfig } from '../../config/constants';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}
// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig('prod')!;

describe('cdk-nag-stateless-stack', () => {
  let stack: OrcaBusStatelessStack;
  let app: App;

  beforeAll(() => {
    app = new App({});
    stack = new OrcaBusStatelessStack(app, 'TestStack', {
      env: {
        account: '12345678',
        region: 'ap-southeast-2',
      },
      ...config.stackProps.orcaBusStatelessConfig,
    });
    Aspects.of(stack).add(new AwsSolutionsChecks());

    // Suppressions (if any)
    //  ...
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
