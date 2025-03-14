#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonFastqUnarchivingLambdaLayerConstructProps {
  layerPrefix: string;
}

export class FastqUnarchivingToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(
    scope: Construct,
    id: string,
    props: PythonFastqUnarchivingLambdaLayerConstructProps
  ) {
    super(scope, id);

    // Generate lambda FastqUnarchiving python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-FastqUnarchiving-py-layer`,
      layerDescription: 'Lambda Layer for handling the fastq unarchiving api via Python',
      layerDirectory: path.join(__dirname, 'fastq_unarchiving_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
