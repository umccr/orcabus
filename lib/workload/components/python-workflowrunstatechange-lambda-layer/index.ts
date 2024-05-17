import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';

export interface PythonWorkflowrunstatechangeLambdaLayerConstructProps {
  layerName: string;
  layerDescription: string;
}

export class PythonWorkflowrunstatechangeLambdaLayerConstruct extends Construct {
  public readonly lambdaLayerArn: string;
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(
    scope: Construct,
    id: string,
    props: PythonWorkflowrunstatechangeLambdaLayerConstructProps
  ) {
    super(scope, id);

    this.lambdaLayerVersionObj = new PythonLayerVersion(this, 'python_lambda_layer', {
      layerVersionName: props.layerName,
      entry: path.join(__dirname, 'workflowrunstatechange-layer'),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
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
