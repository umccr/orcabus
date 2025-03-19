import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { getEnvironmentConfig } from '../../config/config';
import { StatelessStackCollection } from '../../lib/workload/stateless/statelessStackCollectionClass';
import { AppStage } from '../../config/constants';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

// Picking prod environment to test as it contain the sensitive data
const config = getEnvironmentConfig(AppStage.PROD)!;

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

  // FIXME one day we should remove this `AwsSolutions-IAM4` suppression and tackle any use of AWS managed policies
  //  in all our stacks. See https://github.com/umccr/orcabus/issues/174
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

  // NOTE
  // This `AwsSolutions-L1` is tricky. Typically, it is okay to have one version less of the latest runtime
  // version. Not every dependency (including transitive packages) aren't upto speed with latest runtime.
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

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-SF1',
        reason:
          'We do not utilise StepFunction CloudWatch logging feature yet. ' +
          'If turn this feature on, we will hit `AwsSolutions-IAM5` nag. FYI.' +
          'See policy doc in https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html',
      },
    ],
    true
  );

  NagSuppressions.addStackSuppressions(
    stack,
    [
      {
        id: 'AwsSolutions-SF2',
        reason:
          'We do not utilise StepFunction XRay tracing feature yet. ' +
          'https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html ' +
          'If turn this feature on, we will hit `AwsSolutions-IAM5` nag. FYI.' +
          'See policy doc in https://docs.aws.amazon.com/step-functions/latest/dg/xray-iam.html',
      },
    ],
    true
  );

  // for each stack specific

  switch (stackId) {
    case 'SampleSheetCheckerStack':
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/SampleSheetCheckerStack/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: 'Used to deny aws logs to be sent to cloudwatch logs. ',
          },
        ],
        true
      );

      break;

    case 'MetadataManagerStack':
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/MetadataManagerStack/MigrationLambda/AutoMigrateLambdaFunction/Provider/framework-onEvent/ServiceRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              'The provider function needs to be able to invoke the configured function. It uses' +
              "`lambda.Function.grantInvoke` to achieve this which contains a '*' and is not changeable.",
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/MetadataManagerStack/APILambda/APILambda/ServiceRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              `Allow asterisk arn resource to allow any of the lambda version to be invoked ` +
              `from this API lambda`,
          },
        ],
        true
      );
      break;

    case 'FileManagerStack':
      NagSuppressions.addResourceSuppressions(
        stack,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: "'*' is required to access objects in the indexed bucket by filemanager.",
            appliesTo: [
              'Resource::arn:aws:s3:::org.umccr.data.oncoanalyser/*',
              'Resource::arn:aws:s3:::pipeline-prod-cache-503977275616-ap-southeast-2/*',
              'Resource::arn:aws:s3:::archive-prod-analysis-503977275616-ap-southeast-2/*',
              'Resource::arn:aws:s3:::archive-prod-fastq-503977275616-ap-southeast-2/*',
            ],
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressions(
        stack,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: "'*' is required to access any version of the specific user access key secret.",
            appliesTo: [
              'Resource::arn:aws:secretsmanager:ap-southeast-2:472057503814:secret:orcabus/file-manager-presign-user-*',
            ],
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressions(
        stack,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              "'*' is required to access the inventory manifest and data files by the inventory function.",
            appliesTo: ['Resource::arn:aws:s3:::filemanager-inventory-test/*'],
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
        ],
        true
      );
      break;

    case 'DataMigrateStack':
      NagSuppressions.addResourceSuppressions(
        stack,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: "'*' is required to access buckets for moving data.",
            appliesTo: [
              'Resource::arn:aws:s3:::org.umccr.data.oncoanalyser/*',
              'Resource::arn:aws:s3:::pipeline-prod-cache-503977275616-ap-southeast-2/*',
              'Resource::arn:aws:s3:::archive-prod-analysis-503977275616-ap-southeast-2/*',
              'Resource::arn:aws:s3:::archive-prod-fastq-503977275616-ap-southeast-2/*',
            ],
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/DataMigrateStack/StateMachine/Role/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: '* is required to SendTaskSuccess/SendTaskFailure',
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/DataMigrateStack/Role/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: '* is required to SendTaskSuccess/SendTaskFailure',
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/DataMigrateStack/TaskDefinition/ExecutionRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: '* is required to SendTaskSuccess/SendTaskFailure',
          },
        ],
        true
      );
      break;

    case 'SequenceRunManagerStack':
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/SequenceRunManagerStack/LambdaRole/DefaultPolicy/Resource`,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason:
              '* is required to access the temporary linking data files by the enrichment lambda function.',
          },
        ],
        true
      );
      NagSuppressions.addResourceSuppressionsByPath(
        stack,
        `/SequenceRunManagerStack/SrmTempLinkingDataBucket/Resource`,
        [
          {
            id: 'AwsSolutions-S1',
            reason:
              'S3 Bucket has server access logs disabled as temporary linking data files are not accessed by the API, only by the enrichment lambda function',
          },
        ],
        true
      );
      break;

    default:
      break;
  }
}
