
import { Construct } from 'constructs'
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface LambdaLayerConstructProps {
  layer_directory: string
}

export class LambdaLayerConstruct extends Construct {

  public readonly lambda_layer_arn: string;
  public readonly lambda_layer_version_obj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: LambdaLayerConstructProps) {
    super(scope, id);

    this.lambda_layer_version_obj = new PythonLayerVersion(
      this,
      'bclconvert_interop_qc_pipeline_manager_tools',
      {
        entry: props.layer_directory,
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
        compatibleArchitectures: [lambda.Architecture.X86_64],
        license: 'GPL3',
        description: 'A layer to enable the bclconvert interop qc pipeline',
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