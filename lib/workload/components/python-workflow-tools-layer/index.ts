#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../python-lambda-layer';

export interface PythonWorkflowLambdaLayerConstructProps {
  layerPrefix: string;
}

export class WorkflowToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonWorkflowLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda workflow python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-workflow-py-layer`,
      layerDescription: 'Lambda Layer for handling the workflow api via Python',
      layerDirectory: path.join(__dirname, 'workflow_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
