import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { getPythonUvDockerImage } from '../uv-python-lambda-image-builder';

export interface PythonLambdaLayerConstructProps {
  layerName: string;
  layerDirectory: string;
  layerDescription: string;
}

export class PythonLambdaLayerConstruct extends Construct {
  public readonly lambdaLayerArn: string;
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonLambdaLayerConstructProps) {
    super(scope, id);

    // Generate the docker image
    this.lambdaLayerVersionObj = new PythonLayerVersion(this, 'python_lambda_layer', {
      layerVersionName: props.layerName,
      entry: props.layerDirectory,
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      license: 'GPL3',
      description: props.layerDescription,
      bundling: {
        image: getPythonUvDockerImage(),
        commandHooks: {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          beforeBundling(inputDir: string, outputDir: string): string[] {
            return [];
          },
          afterBundling(inputDir: string, outputDir: string): string[] {
            return [
              `pip install ${inputDir} --target ${outputDir}`,
              `find ${outputDir} -name 'pandas' -exec rm -rf {}/tests/ \\;`,
            ];
          },
        },
      },
    });

    // Set outputs
    this.lambdaLayerArn = this.lambdaLayerVersionObj.layerVersionArn;
  }
}
