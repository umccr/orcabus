import { Construct } from 'constructs';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { Duration } from 'aws-cdk-lib';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';

export interface PythonLambdaGetCwlObjectFromS3InputsProps {
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class PythonLambdaGetCwlObjectFromS3InputsConstruct extends Construct {
  public readonly lambdaObj: lambda_python.PythonFunction;

  constructor(scope: Construct, id: string, props: PythonLambdaGetCwlObjectFromS3InputsProps) {
    super(scope, id);

    this.lambdaObj = new lambda_python.PythonFunction(this, 'get_cwl_object_from_s3_inputs_py', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      entry: path.join(__dirname, 'get_cwl_object_from_s3_inputs_py'),
      index: 'get_cwl_object_from_s3_inputs.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(60),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
      },
    });

    /* Give the Lambda permission to access the icav2 secret */
    props.icav2AccessTokenSecretObj.grantRead(this.lambdaObj.currentVersion);
  }
}
