#!/usr/bin/env python3

import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';

interface LambdaUuidGeneratorProps {
  functionNamePrefix: string;
}

export class LambdaUuidGeneratorConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  constructor(scope: Construct, id: string, props: LambdaUuidGeneratorProps) {
    super(scope, id);

    // UUID 7 Generator lambda
    this.lambdaObj = new PythonFunction(this, 'uuid_generator', {
      functionName: `${props.functionNamePrefix}-uuid-generator`,
      entry: path.join(__dirname, 'generate_uuid_py'),
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_uuid.py',
      handler: 'handler',
      memorySize: 1024,
    });
  }
}
