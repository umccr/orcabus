import { DockerImage } from 'aws-cdk-lib';
import path from 'path';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import {
  ParamsAndSecretsLayerVersion,
  ParamsAndSecretsLogLevel,
  ParamsAndSecretsVersions,
} from 'aws-cdk-lib/aws-lambda';

export function getPythonUvDockerImage(): DockerImage {
  return DockerImage.fromBuild(path.join(__dirname, 'build_python'));
}

/**
A Python Lambda function
**/
export class PythonUvFunction extends PythonFunction {
  constructor(scope: Construct, id: string, props: PythonFunctionProps) {
    const uvProps = {
      ...props,
      bundling: {
        ...props.bundling,
        buildArgs: {
          ...props.bundling?.buildArgs,
          // Add TARGETPLATFORM to build args if it's not already set
          TARGETPLATFORM:
            props.bundling?.buildArgs?.TARGETPLATFORM ?? lambda.Architecture.ARM_64.dockerPlatform,
        },
        image: getPythonUvDockerImage(),
        commandHooks: {
          beforeBundling(inputDir: string, outputDir: string): string[] {
            return [];
          },
          afterBundling(inputDir: string, outputDir: string): string[] {
            return [`rm -rf ${outputDir}/pandas/tests`];
          },
        },
      },
      paramsAndSecrets:
        props.paramsAndSecrets ??
        ParamsAndSecretsLayerVersion.fromVersion(ParamsAndSecretsVersions.V1_0_103, {
          cacheEnabled: true,
          cacheSize: 300,
          logLevel: ParamsAndSecretsLogLevel.DEBUG,
        }),
    };
    super(scope, id, uvProps);
  }
}
