#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonFastqLambdaLayerConstructProps {
  layerPrefix: string;
}

export class FastqToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonFastqLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda Fastq python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-Fastq-py-layer`,
      layerDescription: 'Lambda Layer for handling the Fastq api via Python',
      layerDirectory: path.join(__dirname, 'fastq_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
