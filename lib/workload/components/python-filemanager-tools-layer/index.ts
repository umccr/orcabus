#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonFilemanagerLambdaLayerConstructProps {
  layerPrefix: string;
}

export class FilemanagerToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonFilemanagerLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda filemanager python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-filemanager-py-layer`,
      layerDescription: 'Lambda Layer for handling the filemanager api via Python',
      layerDirectory: path.join(__dirname, 'filemanager_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
