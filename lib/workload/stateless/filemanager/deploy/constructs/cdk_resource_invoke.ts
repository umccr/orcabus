import { Construct, IDependable } from 'constructs';
import {
  AwsCustomResource,
  AwsCustomResourcePolicy,
  AwsSdkCall,
  PhysicalResourceId,
} from 'aws-cdk-lib/custom-resources';
import * as fn from './functions/function';
import { CfnOutput, Stack, Token } from 'aws-cdk-lib';
import { IVpc, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { ManagedPolicy, PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';

/**
 * Props for the resource invoke construct.
 */
export type CdkResourceInvokeProps = {
  /**
   * Vpc for the function.
   */
  vpc: IVpc;
  /**
   * The function to create. This will override the function name to ensure that it remains
   * callable using the singleton function created by `AwsCustomResource`. See
   * https://github.com/aws-samples/amazon-rds-init-cdk/blob/239626632f399ebe4928410a49d5ac5d009a6502/lib/resource-initializer.ts#L69-L71.
   */
  createFunction: (scope: Construct, id: string, props: fn.FunctionPropsNoPackage) => fn.Function;
  /**
   * Function props when creating the Lambda function.
   */
  functionProps: fn.FunctionPropsNoPackage;
  /**
   * Name to use when creating the function.
   */
  id: string;
  /**
   * Dependencies for this resource.
   */
  dependencies?: IDependable[];
};

/**
 * A construct for invoking a Lambda function for resource initialization.
 */
export class CdkResourceInvoke extends Construct {
  private readonly _response: string;
  private readonly _customResource: AwsCustomResource;
  private readonly _function: fn.Function;

  constructor(scope: Construct, id: string, props: CdkResourceInvokeProps) {
    super(scope, id);

    const stack = Stack.of(this);
    this._function = props.createFunction(this, props.id, {
      ...props.functionProps,
      functionName: `${stack.stackName}-ResourceInvokeFunction-${props.id}`,
    });

    // Call another lambda function with no arguments.
    const sdkCall: AwsSdkCall = {
      service: 'Lambda',
      action: 'invoke',
      parameters: {
        FunctionName: this.function.functionName(),
      },
      physicalResourceId: PhysicalResourceId.of(
        `${id}-AwsSdkCall-${this.function.currentVersion()}`
      ),
    };

    const role = new Role(this, 'AwsCustomResourceRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
    });
    role.addToPolicy(
      new PolicyStatement({
        resources: [
          // This needs to have permissions to run any `ResourceInvokeFunction` because it is deployed as a
          // singleton Lambda function.
          `arn:aws:lambda:${stack.region}:${stack.account}:function:${stack.stackName}-ResourceInvokeFunction-*`,
        ],
        actions: ['lambda:InvokeFunction'],
      })
    );
    // Also require VPC access for a Lambda function within the VPC.
    role.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole')
    );

    this._customResource = new AwsCustomResource(this, 'AwsCustomResource', {
      policy: AwsCustomResourcePolicy.fromSdkCalls({
        resources: AwsCustomResourcePolicy.ANY_RESOURCE,
      }),
      onUpdate: sdkCall,
      role: role,
      vpc: props.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
    });

    this._response = this.customResource.getResponseField('Payload');

    // Add any dependencies.
    props.dependencies?.forEach((dependency) => this.addDependency(dependency));

    // Output the result.
    new CfnOutput(this, 'MigrateDatabaseResponse', {
      value: Token.asString(this.response),
    });
  }

  /**
   * Add a dependency to this resource.
   */
  addDependency(dependency: IDependable) {
    this.customResource.node.addDependency(dependency);
  }

  /**
   * Get the function response.
   */
  get response(): string {
    return this._response;
  }

  /**
   * Get the custom resource.
   */
  get customResource(): AwsCustomResource {
    return this._customResource;
  }

  /**
   * Get the function.
   */
  get function(): fn.Function {
    return this._function;
  }
}
