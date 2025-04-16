#!/usr/bin/env python3

import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';

export interface PythonFastqSyncLambdaLayerConstructProps {
  layerPrefix: string;
}

export class FastqSyncToolsPythonLambdaLayer extends Construct {
  public readonly lambdaLayerVersionObj: PythonLayerVersion;

  constructor(scope: Construct, id: string, props: PythonFastqSyncLambdaLayerConstructProps) {
    super(scope, id);

    // Generate lambda Fastq python layer
    // Get lambda layer object
    this.lambdaLayerVersionObj = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerName: `${props.layerPrefix}-Fastq-Sync-py-layer`,
      layerDescription: 'Lambda Layer for handling the Fastq sync via Python',
      layerDirectory: path.join(__dirname, 'fastq_sync_tools_layer'),
    }).lambdaLayerVersionObj;
  }
}
