import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

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

    this.lambdaLayerVersionObj = new PythonLayerVersion(this, 'python_lambda_layer', {
      layerVersionName: props.layerName,
      entry: props.layerDirectory,
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      license: 'GPL3',
      description: props.layerDescription,
      bundling: {
        commandHooks: {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          beforeBundling(inputDir: string, outputDir: string): string[] {
            return [];
          },
          afterBundling(inputDir: string, outputDir: string): string[] {
            return [`python -m pip install ${inputDir} -t ${outputDir}`];
          },
        },
      },
    });

    // Set outputs
    this.lambdaLayerArn = this.lambdaLayerVersionObj.layerVersionArn;
  }
}
