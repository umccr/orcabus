import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';

export interface bsshFastqCopyManagerInputMakerConstructProps {
  layerName?: string;
  layerDescription?: string;
}

export class bsshFastqCopyManagerInputMakerConstruct extends Construct {
  public readonly lambdaLayerArn: string;
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: bsshFastqCopyManagerInputMakerConstructProps) {
    super(scope, id);
    // TODO
  }
}
