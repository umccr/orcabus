#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonBsshLambdaLayerConstructProps {
  layerPrefix: string;
}

export class BsshToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonBsshLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda filemanager python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-bssh-py-layer`,
      layerDescription: 'Lambda Layer for handling the bssh tools via Python',
      layerDirectory: path.join(__dirname, 'bssh_manager_tools/src'),
    }).lambdaLayerVersionObj;
  }
}
