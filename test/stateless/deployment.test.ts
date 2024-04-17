import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { getEnvironmentConfig } from '../../config/config';
import { StatelessStackCollection } from '../../lib/workload/stateless/statelessStackCollectionClass';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig('prod')!;

describe('cdk-nag-stateless-stack', () => {
  const app: App = new App({});

  const stackCollection = new StatelessStackCollection(
    app,
    {
      account: '123456789',
      region: 'ap-southeast-2',
    },
    config.stackProps.statelessConfig
  );

  for (const key in stackCollection) {
    if (Object.prototype.hasOwnProperty.call(stackCollection, key)) {
      const stack = stackCollection[key as keyof StatelessStackCollection];
      const stackId = stack.node.id;

      Aspects.of(stack).add(new AwsSolutionsChecks());
      applyNagSuppression(stackId, stack);

      test(`${stackId}: cdk-nag AwsSolutions Pack errors`, () => {
        const errors = Annotations.fromStack(stack)
          .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
          .map(synthesisMessageToString);
        expect(errors).toHaveLength(0);
      });

      test(`${stackId}: cdk-nag AwsSolutions Pack warnings`, () => {
        const warnings = Annotations.fromStack(stack)
          .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
          .map(synthesisMessageToString);
        expect(warnings).toHaveLength(0);
      });
    }
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
    [{ id: 'AwsSolutions-IAM4', reason: 'allow to use AWS managed policy' }],
    true
  );

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-APIG1',
        reason: 'See https://github.com/aws/aws-cdk/issues/11100',
      },
    ],
    true
  );

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-APIG4',
        reason: 'We have the default Cognito UserPool authorizer',
      },
    ],
    true
  );

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-L1',
        reason: "'AwsCustomResource' is out of date",
      },
    ],
    true
  );

  // for each stack specific

  switch (stackId) {
    case 'FileManagerStack':
      NagSuppressions.addResourceSuppressions(
        stack,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: "'*' is required to access objects in the indexed bucket by filemanager.",
            appliesTo: ['Resource::arn:aws:s3:::org.umccr.data.oncoanalyser/*'],
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/FileManagerStack/MigrateProviderFunction/Provider/framework-onEvent/ServiceRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'The provider function needs to be able to invoke the configured function. It uses' +
              "`lambda.Function.grantInvoke` to achieve this which contains a '*' and is not changeable.",
          },
        ]
      );
      break;

    default:
      break;
  }
}
