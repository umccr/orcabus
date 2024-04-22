import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';

import { getEnvironmentConfig } from '../../../config/config';
import { StatefulStackCollection } from '../../../lib/workload/stateful/statefulStackCollectionClass';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig('prod')!;

describe('cdk-nag-stateful-stack', () => {
  const app: App = new App();

  const stackCollection = new StatefulStackCollection(
    app,
    {
      account: '12345678',
      region: 'ap-southeast-2',
    },
    config.stackProps.statefulConfig
  );

  for (const key in stackCollection) {
    if (Object.prototype.hasOwnProperty.call(stackCollection, key)) {
      const stack = stackCollection[key as keyof StatefulStackCollection];

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
          '/TokenServiceStack/ServiceUserRole/DefaultPolicy/Resource',
          '/TokenServiceStack/JWTRole/DefaultPolicy/Resource',
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
    case 'SharedStack':
      // suppress by resource
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        [
          '/SharedStack/EventBusConstruct/UniversalEventArchiver/UniversalEventArchiver/ServiceRole/Resource',
          '/SharedStack/EventBusConstruct/UniversalEventArchiver/UniversalEventArchiver/ServiceRole/DefaultPolicy/Resource',
        ],
        [
          {
            id: 'AwsSolutions-IAM4',
            reason:
              'AWSLambdaBasicExecutionRole,AWSLambdaVPCAccessExecutionRole are needed. See ' +
              'https://stackoverflow.com/questions/45282492/s3-policy-to-allow-lambda ' +
              'https://repost.aws/knowledge-center/lambda-execution-role-s3-bucket ' +
              'https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html ',
          },
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'Permission to <EventBusConstructUniversalEventArchiveBucketxxxx.Arn>/* is needed. See ' +
              'https://stackoverflow.com/questions/45282492/s3-policy-to-allow-lambda ' +
              'https://repost.aws/knowledge-center/lambda-execution-role-s3-bucket ' +
              'https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html ',
          },
        ]
      );
      break;

    default:
      break;
  }
}
