
import { Construct } from 'constructs'
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface LambdaLayerConstructProps {
  layer_directory: string
  layer_name: string
}

export class LambdaLayerConstruct extends Construct {

  public readonly lambda_layer_arn: string;
  public readonly lambda_layer_version_obj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: LambdaLayerConstructProps) {
    super(scope, id);

    this.lambda_layer_version_obj = new PythonLayerVersion(
      this,
      `tool_layer_${props.layer_name}`,
      {
        entry: props.layer_directory,
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
        compatibleArchitectures: [lambda.Architecture.X86_64],
        license: 'GPL3',
        description: `A layer to enable the lambda runtime ${props.layer_name}`,
        bundling: {
          commandHooks: {
            beforeBundling(inputDir: string, outputDir: string): string[] {
              return [];
            },
            afterBundling(inputDir: string, outputDir: string): string[] {
              return [
                `python -m pip install ${inputDir} -t ${outputDir}`,
              ];
            },
          },
        },
      });

    // Set outputs
    this.lambda_layer_arn = this.lambda_layer_version_obj.layerVersionArn;
  }
}