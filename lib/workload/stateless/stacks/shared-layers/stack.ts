import { Construct } from 'constructs';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { Stack, StackProps } from 'aws-cdk-lib';
import { ExecutionServiceCodeBindingLayerConstruct } from './constructs/executionservice-codebinding-layer';

export class SharedLayersStack extends Stack {
  public readonly executionServiceCodeBindingLayer: PythonLayerVersion;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    this.executionServiceCodeBindingLayer = new ExecutionServiceCodeBindingLayerConstruct(
      this,
      'ExecutionServiceCodeBindingLayer'
    ).lambdaLayerVersionObj;
  }
}
