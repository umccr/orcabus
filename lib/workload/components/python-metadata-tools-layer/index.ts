#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonMetadataLambdaLayerConstructProps {
  layerPrefix: string;
}

export class MetadataToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonMetadataLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda metadata python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-metadata-py-layer`,
      layerDescription: 'Lambda Layer for handling the metadata api via Python',
      layerDirectory: path.join(__dirname, 'metadata_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
