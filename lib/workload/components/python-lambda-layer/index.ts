import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface PythonLambdaLayerConstructProps {
  layer_name: string;
  layer_directory: string;
  layer_description: string;
}

export class PythonLambdaLayerConstruct extends Construct {
  public readonly lambda_layer_arn: string;
  public readonly lambda_layer_version_obj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonLambdaLayerConstructProps) {
    super(scope, id);

    this.lambda_layer_version_obj = new PythonLayerVersion(this, 'python_lambda_layer', {
      layerVersionName: props.layer_name,
      entry: props.layer_directory,
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      license: 'GPL3',
      description: props.layer_description,
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
    this.lambda_layer_arn = this.lambda_layer_version_obj.layerVersionArn;
  }
}
