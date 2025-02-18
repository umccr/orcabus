import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';

import { getEnvironmentConfig } from '../../../config/config';
import { StatefulStackCollection } from '../../../lib/workload/stateful/statefulStackCollectionClass';
import { AppStage } from '../../../config/constants';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig(AppStage.PROD)!;

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

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-L1',
        reason:
          'Use the latest available runtime for the targeted language to avoid technical debt. ' +
          'Runtimes specific to a language or framework version are deprecated when the version ' +
          'reaches end of life. This rule only applies to non-container Lambda functions.',
      },
    ],
    true
  );

  // for each stack specific
  switch (stackId) {
    case 'AuthorizationManagerStack':
      // FIXME - https://github.com/umccr/orcabus/issues/174
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        // pragma: allowlist nextline secret
        ['/AuthorizationManagerStack/HTTPLambdaAuthorizer/ServiceRole/Resource'],
        [
          {
            id: 'AwsSolutions-IAM4',
            reason: 'Tracking this at (https://github.com/umccr/orcabus/issues/174)',
          },
        ]
      );
      break;
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
          '/SharedStack/EventBusConstruct/UniversalEventArchiveBucket/Resource',
          '/SharedStack/EventBusConstruct/UniversalEventArchiver/UniversalEventArchiver/ServiceRole/Resource',
          '/SharedStack/EventBusConstruct/UniversalEventArchiver/UniversalEventArchiver/ServiceRole/DefaultPolicy/Resource',
          '/SharedStack/DatabaseConstruct/Cluster/MonitoringRole/Resource',
          '/SharedStack/DatabaseConstruct/OrcaBusDatabaseTier2BackupPlan/OrcaBusDatabaseTier2BackupSelection/Role/Resource',
        ],
        [
          {
            id: 'AwsSolutions-S1',
            reason:
              'This is no necessity to retain the server access logs for Event Archiver Bucket.',
          },
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
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        '/SharedStack/OrcabusEventDlqFmannotator/Resource',
        [
          {
            id: 'AwsSolutions-SQS3',
            reason:
              'it is expected that the DLQ construct has a Queue without a DLQ, because that ' +
              'queue itself acts as the DLQ for other constructs.',
          },
        ],
        true
      );
      break;

    case 'PostgresManagerStack':
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/PostgresManagerStack/UpdatePgProviderFunction/Provider/framework-onEvent/ServiceRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'The provider function needs to be able to invoke the configured function. It uses' +
              "`lambda.Function.grantInvoke` to achieve this which contains a '*' and is not changeable.",
          },
        ]
      );

      // FIXME one day we should remove this `AwsSolutions-IAM4` suppression and tackle any use of AWS managed policies
      //  in all our stacks. See https://github.com/umccr/orcabus/issues/174
      NagSuppressions.addStackSuppressions(
        stack,
        [{ id: 'AwsSolutions-IAM4', reason: 'allow to use AWS managed policy' }],
        true
      );
      break;

    case 'AccessKeySecretStack':
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        [
          '/AccessKeySecretStack/User/DefaultPolicy/Resource',
          '/AccessKeySecretStack/Secret/Resource',
        ],
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'Wildcard is required to have read-only access to the bucket for pre-signing URLs.',
          },
          {
            id: 'AwsSolutions-SMG4',
            reason: 'Automatic secret rotation is a todo.',
          },
        ]
      );
      break;

    default:
      break;
  }
}
