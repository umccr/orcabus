import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export interface LambdaLayerConstructProps {
  layer_directory: string;
}

export class LambdaLayerConstruct extends Construct {
  public readonly lambda_layer_arn: string;
  public readonly lambda_layer_version_obj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: LambdaLayerConstructProps) {
    super(scope, id);

    this.lambda_layer_version_obj = new PythonLayerVersion(this, 'cttso_v2_tool_layer', {
      entry: props.layer_directory,
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      license: 'GPL3',
      description: 'A layer to enable the cttso_v2 manager tools layer',
      bundling: {
        commandHooks: {
          beforeBundling(inputDir: string, outputDir: string): string[] {
            return [];
          },
          afterBundling(inputDir: string, outputDir: string): string[] {
            return [
              `python -m pip install ${inputDir} -t ${outputDir}`,
              `find ${outputDir} -type d -name "pandas" -exec echo rm -rf {}/tests \;`,
            ];
          },
        },
      },
    });

    // Set outputs
    this.lambda_layer_arn = this.lambda_layer_version_obj.layerVersionArn;
  }
}
