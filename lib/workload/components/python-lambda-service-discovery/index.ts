import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { NagSuppressions } from 'cdk-nag';

interface LambdaServiceDiscoveryProps {
  functionNamePrefix: string;
}

export class LambdaServiceDiscoveryConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  constructor(scope: Construct, id: string, props: LambdaServiceDiscoveryProps) {
    super(scope, id);

    // ServiceDiscovery lambda
    this.lambdaObj = new PythonFunction(this, 'service_discovery_py', {
      functionName: `${props.functionNamePrefix}-service-discovery`,
      entry: path.join(__dirname, 'service_discovery_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'service_discovery.py',
      handler: 'handler',
      memorySize: 1024,
    });

    // Grant permissions to the lambda
    this.lambdaObj.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['servicediscovery:ListServices'],
        resources: ['*'],
      })
    );

    // Suppress CDK NAGs
    NagSuppressions.addResourceSuppressions(
      this.lambdaObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Need to run the ListServices against all services',
        },
      ],
      true
    );
  }
}
