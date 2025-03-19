import { DockerImage } from 'aws-cdk-lib';
import path from 'path';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { Construct } from 'constructs';

export function getPythonUvDockerImage(): DockerImage {
  return DockerImage.fromBuild(path.join(__dirname));
}

/**
 * A Python Lambda function
 */
export class PythonUvFunction extends PythonFunction {
  constructor(scope: Construct, id: string, props: PythonFunctionProps) {
    const uvProps = {
      ...props,
      bundling: {
        ...props.bundling,
        image: getPythonUvDockerImage(),
      },
    };
    super(scope, id, uvProps);
  }
}
