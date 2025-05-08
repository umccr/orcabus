#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonSequenceLambdaLayerConstructProps {
  layerPrefix: string;
}

export class SequenceToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonSequenceLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda sequence python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-sequence-py-layer`,
      layerDescription: 'Lambda Layer for handling the sequence api via Python',
      layerDirectory: path.join(__dirname, 'sequence_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
