import { Construct, IDependable } from 'constructs';
import {
  AwsCustomResource,
  AwsCustomResourcePolicy,
  AwsSdkCall,
  PhysicalResourceId,
} from 'aws-cdk-lib/custom-resources';
import { CfnOutput, Stack, Token } from 'aws-cdk-lib';
import { IVpc, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { ManagedPolicy, PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Version } from 'aws-cdk-lib/aws-lambda';
import { createHash } from 'node:crypto';

/**
 * The interface by which the generic type of `CdkResourceInvoke` is constrained by.
 * Note that the standard `lambda.Function` meets this constraint, which means it can
 * be used directly with the `CdkResourceInvoke`, rather than having to wrap it in
 * another class.
 */
export interface InvokeFunction {
  /**
   * The function name to be used when constructing the invoke function.
   */
  functionName?: string;
  /**
   * The current version of the function.
   */
  currentVersion: Version;
}

/**
 * An interface representing the function name that is created when using `CdkResourceInvoke`.
 */
export type FunctionName = {
  /**
   * Function name.
   */
  functionName: string;
};

/**
 * Props for the resource invoke construct.
 */
export type CdkResourceInvokeProps<P, F extends InvokeFunction> = {
  /**
   * Vpc for the function.
   */
  vpc: IVpc;
  /**
   * The function to create. This will override any `functionName` property to ensure that it remains
   * callable using the singleton function created by `AwsCustomResource`. See
   * https://github.com/aws-samples/amazon-rds-init-cdk/blob/239626632f399ebe4928410a49d5ac5d009a6502/lib/resource-initializer.ts#L69-L71.
   *
   * It is expected that this creates a Lambda function with the `functionName`. This allows `CdkResourceInvoke`
   * to call the function after it is created.
   */
  createFunction: (scope: Construct, id: string, props: FunctionName & P) => F;
  /**
   * Function props when creating the Lambda function.
   */
  functionProps: P;
  /**
   * Name to use when creating the function.
   */
  id: string;
  /**
   * Dependencies for this resource.
   */
  dependencies?: IDependable[];
  /**
   * Any payload to pass to the Lambda function.
   */
  payload?: string;
};

/**
 * A construct for invoking a Lambda function for resource initialization. This is useful for performing
 * database actions such as migrations during CloudFormation stack creation, to ensure that a database is
 * in the expected state before the stack succeeds.
 */
export class CdkResourceInvoke<P, F extends InvokeFunction> extends Construct {
  private readonly _response: string;
  private readonly _customResource: AwsCustomResource;
  private readonly _function: F;

  constructor(scope: Construct, id: string, props: CdkResourceInvokeProps<P, F>) {
    super(scope, id);

    const stack = Stack.of(this);

    // It's necessary to hash this because stack names can exceed the 64 character limit of function names.
    const stackHash = this.hashValue(stack.stackName);
    this._function = props.createFunction(this, props.id, {
      ...props.functionProps,
      functionName: `${stackHash}-ResourceInvokeFunction-${props.id}`,
    });

    // Call another lambda function with no arguments.
    const sdkCall: AwsSdkCall = {
      service: 'Lambda',
      action: 'invoke',
      parameters: {
        FunctionName: this.function.functionName,
        ...(props.payload && { Payload: props.payload }),
      },
      physicalResourceId: PhysicalResourceId.of(
        `${id}-AwsSdkCall-${this.function.currentVersion + this.hashValue(props.payload)}`
      ),
    };

    const role = new Role(this, 'AwsCustomResourceRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
    });
    const lambdaResource = `arn:aws:lambda:${stack.region}:${stack.account}:function:${stackHash}-ResourceInvokeFunction-${props.id}`;
    role.addToPolicy(
      new PolicyStatement({
        resources: [lambdaResource],
        actions: ['lambda:InvokeFunction'],
      })
    );
    // Also require VPC access for a Lambda function within the VPC.
    role.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole')
    );

    this._customResource = new AwsCustomResource(this, 'AwsCustomResource', {
      policy: AwsCustomResourcePolicy.fromSdkCalls({
        resources: [lambdaResource],
      }),
      onUpdate: sdkCall,
      role: role,
      vpc: props.vpc,
      installLatestAwsSdk: true,
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

  private hashValue(value?: string): string {
    if (!value) {
      return '';
    }

    return createHash('md5').update(value).digest('hex').substring(0, 24);
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
  get function(): F {
    return this._function;
  }
}
