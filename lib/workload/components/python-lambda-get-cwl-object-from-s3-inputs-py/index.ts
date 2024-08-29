import { Construct } from 'constructs';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { Duration } from 'aws-cdk-lib';

export class PythonLambdaGetCwlObjectFromS3InputsConstruct extends Construct {
  public readonly lambdaObj: lambda_python.PythonFunction;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.lambdaObj = new lambda_python.PythonFunction(this, 'get_cwl_object_from_s3_inputs_py', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      entry: path.join(__dirname, 'get_cwl_object_from_s3_inputs_py'),
      index: 'get_cwl_object_from_s3_inputs.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(10),
    });
  }
}
