import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';

interface LambdaB64GzTranslatorProps {
  functionNamePrefix: string;
}

export class LambdaB64GzTranslatorConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  constructor(scope: Construct, id: string, props: LambdaB64GzTranslatorProps) {
    super(scope, id);

    // UUID 7 Generator lambda
    this.lambdaObj = new PythonFunction(this, 'b64_gzip_translator_obj', {
      functionName: `${props.functionNamePrefix}-b64gz-t`,
      entry: path.join(__dirname, 'b64gz_translator_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'b64gz_translator.py',
      handler: 'handler',
      memorySize: 1024,
    });
  }
}
