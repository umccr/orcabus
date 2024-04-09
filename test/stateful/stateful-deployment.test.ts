import { App, Aspects, Stack } from 'aws-cdk-lib';
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
  const app: App = new App();
  const stack: OrcaBusStatefulStack = new OrcaBusStatefulStack(app, 'TestStack', {
    env: {
      account: '12345678',
      region: 'ap-southeast-2',
    },
    ...config.stackProps.orcaBusStatefulConfig,
  });

  beforeAll(() => {
    Aspects.of(stack).add(new AwsSolutionsChecks());

    // Suppress CDK-NAG for secret rotation
    NagSuppressions.addStackSuppressions(stack, [
      { id: 'AwsSolutions-APIG1', reason: 'See https://github.com/aws/aws-cdk/issues/11100' },
    ]);
  });
  // FIXME
  //  perhaps just need the following code after refactoring `OrcaBusDatabaseConstruct` => `DatabaseStack`
  //  instead of code block from the above^^ `beforeAll(..)` ~victor
  //Aspects.of(stack).add(new AwsSolutionsChecks());
  //applyNagSuppression(stack.node.id, stack);

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

  // per-stateful stack cdk-nag test
  for (const s of stack.statefulStackArray) {
    const stackId = s.node.id;

    Aspects.of(s).add(new AwsSolutionsChecks());

    applyNagSuppression(stackId, s);

    test(`${stackId}: cdk-nag AwsSolutions Pack errors`, () => {
      const errors = Annotations.fromStack(s)
        .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
        .map(synthesisMessageToString);
      expect(errors).toHaveLength(0);
    });

    test(`${stackId}: cdk-nag AwsSolutions Pack warnings`, () => {
      const warnings = Annotations.fromStack(s)
        .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
        .map(synthesisMessageToString);
      expect(warnings).toHaveLength(0);
    });
  }
});

/**
 * apply nag suppression according to the relevant stackId
 * @param stackId the stackId
 * @param stack
 */
function applyNagSuppression(stackId: string, stack: Stack) {
  // all stacks widely
  NagSuppressions.addStackSuppressions(
    stack,
    [{ id: 'AwsSolutions-APIG1', reason: 'See https://github.com/aws/aws-cdk/issues/11100' }],
    true
  );

  // for each stack specific
  switch (stackId) {
    case 'TokenServiceStack':
      // suppress by resource
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        [
          '/TestStack/TokenServiceStack/ServiceUserRole/DefaultPolicy/Resource',
          '/TestStack/TokenServiceStack/JWTRole/DefaultPolicy/Resource',
        ],
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'See ' +
              'https://github.com/aws/aws-cdk/issues/7016 ' +
              'https://github.com/aws/aws-cdk/issues/26611 ' +
              'https://stackoverflow.com/questions/71929482/how-to-prevent-generating-default-policies-during-iam-role-creation-in-aws-cdk',
          },
        ]
      );
      break;

    default:
      break;
  }
}
