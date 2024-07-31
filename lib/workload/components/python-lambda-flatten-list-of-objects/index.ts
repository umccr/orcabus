import { Construct } from 'constructs';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { Duration } from 'aws-cdk-lib';

export class PythonLambdaFlattenListOfObjectsConstruct extends Construct {
  public readonly lambdaObj: lambda_python.PythonFunction;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.lambdaObj = new lambda_python.PythonFunction(this, 'flatten_list_python_function', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      entry: path.join(__dirname, 'flatten_list_of_objects_py'),
      index: 'flatten_list_of_objects.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(3),
    });
  }
}
