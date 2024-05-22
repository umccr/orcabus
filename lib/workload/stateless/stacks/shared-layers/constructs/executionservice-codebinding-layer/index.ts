import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { CfnOutput } from 'aws-cdk-lib';

export class ExecutionServiceCodeBindingLayerConstruct extends Construct {
  public readonly lambdaLayerVersionArn: string;
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.lambdaLayerVersionObj = new PythonLayerVersion(this, 'SchemasCodeBindingLayer', {
      layerVersionName: 'SchemasCodeBindingLayer',
      entry: path.join(__dirname, '../../layers/excecutionservice'),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      description: 'Layer to enable code binding for OrcaBus Event Schemas.',
    });

    // Set outputs
    this.lambdaLayerVersionArn = this.lambdaLayerVersionObj.layerVersionArn;

    new CfnOutput(this, 'lambdaLayerVersionArn', {
      value: this.lambdaLayerVersionArn,
      description: 'The ARN for SchemasCodeBinding Lambda Layer.',
    });
  }
}
