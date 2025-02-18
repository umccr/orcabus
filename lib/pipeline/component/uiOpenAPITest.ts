import { RemovalPolicy } from 'aws-cdk-lib';
import { BuildSpec, ComputeType, LinuxArmBuildImage } from 'aws-cdk-lib/aws-codebuild';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { CodeBuildStep } from 'aws-cdk-lib/pipelines';
import { Construct } from 'constructs';
import { AppStage } from '../../../config/constants';

export type UiSchemaTypeTestProps = {
  testStage: AppStage;
};

export class UiOpenAPITestStep extends CodeBuildStep {
  /**
   * Typescript check the deployed OpenAPI schema against the expected UI schema using the {domainName}/schema/openapi.json endpoint.
   */
  constructor(scope: Construct, id: string, props: UiSchemaTypeTestProps) {
    let umccrDomainName = 'umccr.org';
    if (props.testStage === AppStage.GAMMA) {
      umccrDomainName = 'stg.umccr.org';
    } else if (props.testStage === AppStage.BETA) {
      umccrDomainName = 'dev.umccr.org';
    } else if (props.testStage === AppStage.PROD) {
      umccrDomainName = 'prod.umccr.org';
    }

    super(id, {
      installCommands: [
        // This CodeBuildStep runs inside CodePipeline and sources artifacts from the previous step.
        // To avoid interference with the `orca-ui` artifact, we delete all existing files and start with a fresh directory.
        // We use the deployed endpoints to perform the checks.
        'rm -rf .[^.]*',
        'rm -rf *',

        'node -v',
        'corepack enable',

        // Git clone the UI repo for testing
        // since this is a public repo we could clone it directly
        'git --version',
        'git clone --branch main https://github.com/umccr/orca-ui.git',
        'cd orca-ui',

        'yarn --version',
        'yarn install --immutable',
      ],
      commands: ['set -eu', 'make generate-openapi-types', 'yarn tsc-check'],
      buildEnvironment: {
        computeType: ComputeType.SMALL,
        buildImage: LinuxArmBuildImage.AMAZON_LINUX_2023_STANDARD_3_0,
      },
      partialBuildSpec: BuildSpec.fromObject({
        env: {
          variables: {
            VITE_METADATA_URL: `https://metadata.${umccrDomainName}`,
            VITE_WORKFLOW_URL: `https://workflow.${umccrDomainName}`,
            VITE_SEQUENCE_RUN_URL: `https://sequence.${umccrDomainName}`,
            VITE_FILE_URL: `https://file.${umccrDomainName}`,
          },
        },
        phases: {
          install: {
            'runtime-versions': {
              nodejs: 20,
            },
          },
        },
        version: 0.2,
      }),
      logging: {
        cloudWatch: {
          logGroup: new LogGroup(scope, `UiBackendTypeTest`, {
            removalPolicy: RemovalPolicy.DESTROY,
            retention: RetentionDays.TWO_WEEKS,
          }),
        },
      },
    });
  }
}
