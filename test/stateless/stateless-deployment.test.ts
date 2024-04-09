import { App, Aspects, Stack } from 'aws-cdk-lib';
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
  const app: App = new App({});
  const stack: OrcaBusStatelessStack = new OrcaBusStatelessStack(app, 'TestStack', {
    env: {
      account: '12345678',
      region: 'ap-southeast-2',
    },
    ...config.stackProps.orcaBusStatelessConfig,
  });

  // stateless stack cdk-nag test
  Aspects.of(stack).add(new AwsSolutionsChecks());
  applyNagSuppression(stack.node.id, stack);

  test(`OrcaBusStatelessStack: cdk-nag AwsSolutions Pack errors`, () => {
    const errors = Annotations.fromStack(stack)
      .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(errors).toHaveLength(0);
  });

  test(`OrcaBusStatelessStack: cdk-nag AwsSolutions Pack warnings`, () => {
    const warnings = Annotations.fromStack(stack)
      .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(warnings).toHaveLength(0);
  });

  // microservice cdk-nag test
  for (const ms_stack of stack.microserviceStackArray) {
    const stackId = ms_stack.node.id;

    Aspects.of(ms_stack).add(new AwsSolutionsChecks());

    applyNagSuppression(stackId, ms_stack);

    test(`${stackId}: cdk-nag AwsSolutions Pack errors`, () => {
      const errors = Annotations.fromStack(ms_stack)
        .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
        .map(synthesisMessageToString);
      expect(errors).toHaveLength(0);
    });

    test(`${stackId}: cdk-nag AwsSolutions Pack warnings`, () => {
      const warnings = Annotations.fromStack(ms_stack)
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
    case 'PostgresManager':
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
      break;

    case 'Filemanager':
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
        `/TestStack/Filemanager/MigrateDatabase/Provider/framework-onEvent/ServiceRole/DefaultPolicy/Resource`,
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
