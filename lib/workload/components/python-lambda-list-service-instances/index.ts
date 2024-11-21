import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { NagSuppressions } from 'cdk-nag';

interface LambdaDiscoverInstancesProps {
  functionNamePrefix: string;
}

export class LambdaDiscoverInstancesConstruct extends Construct {
  public readonly lambdaObj: PythonFunction;

  constructor(scope: Construct, id: string, props: LambdaDiscoverInstancesProps) {
    super(scope, id);

    // ServiceDiscovery lambda
    this.lambdaObj = new PythonFunction(this, 'list_service_instances_py', {
      functionName: `${props.functionNamePrefix}-list-service-instances`,
      entry: path.join(__dirname, 'list_service_instances_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'list_service_instances.py',
      handler: 'handler',
      memorySize: 1024,
    });

    // Grant permissions to the lambda
    this.lambdaObj.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'servicediscovery:ListInstances',
          'servicediscovery:DiscoverInstances',
          'servicediscovery:GetService',
        ],
        resources: ['*'],
      })
    );

    // Suppress CDK NAGs
    NagSuppressions.addResourceSuppressions(
      this.lambdaObj,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Need to run the DiscoverInstances against all services since we dont know which one will be used',
        },
      ],
      true
    );
  }
}
