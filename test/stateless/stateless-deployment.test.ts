import { App, Aspects } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
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

    NagSuppressions.addStackSuppressions(stack, [
      { id: 'AwsSolutions-IAM4', reason: 'allow to use AWS managed policy' },
    ]);

    // suppress by resource
    NagSuppressions.addResourceSuppressionsByPath(
      stack,
      `/TestStack/PostgresManager/CreateUserPassPostgresLambda/ServiceRole/DefaultPolicy/Resource`,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            "'*' is required for secretsmanager:GetRandomPassword and new SM ARN will contain random character",
        },
      ]
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
