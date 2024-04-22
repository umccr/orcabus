import { Construct } from 'constructs';
import { Provider } from 'aws-cdk-lib/custom-resources';
import { IVpc, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { CfnFunction, IFunction } from 'aws-cdk-lib/aws-lambda';
import { CfnResource, CustomResource } from 'aws-cdk-lib';
import CodeProperty = CfnFunction.CodeProperty;

/**
 * Props for the resource invoke construct.
 */
export type ProviderFunctionProps = {
  /**
   * Vpc for the function.
   */
  vpc: IVpc;
  /**
   * The provider function.
   */
  function: IFunction;
  /**
   * Properties that get defined in the template and passed to the Lambda function via `ResourceProperties`.
   */
  resourceProperties?: { [keys: string]: unknown };
  /**
   * An additional hash property that can be used to determine if the custom resource should be updated. By default,
   * this is the s3Key of the Lambda code asset, which is derived from the asset hash. This is used to ensure that
   * the custom resource is updated whenever the Lambda function changes, so that the function gets called again.
   * Add a constant value here to override this behaviour.
   */
  additionalHash?: string;
};

/**
 * A construct for invoking a Lambda function using the CDK provider framework:
 * https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html#provider-framework.
 *
 * This is useful for performing database actions such as migrations during CloudFormation stack creation, where CDK
 * deployment will fail if the function fails. To use this construct the Lambda function must return values according
 * to the provider framework.
 */
export class ProviderFunction extends Construct {
  private readonly _function: IFunction;
  private readonly _response: string;

  constructor(scope: Construct, id: string, props: ProviderFunctionProps) {
    super(scope, id);

    this._function = props.function;

    const provider = new Provider(this, 'Provider', {
      onEventHandler: props.function,
      vpc: props.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
    });
    const customResource = new CustomResource(this, 'CustomResource', {
      serviceToken: provider.serviceToken,
      properties: props.resourceProperties,
    });

    // Update the custom resource with an additional key.
    (customResource.node.defaultChild as CfnResource).addPropertyOverride(
      'S3Key',
      props.additionalHash ??
        ((this._function.node.defaultChild as CfnFunction).code as CodeProperty).s3Key
    );

    this._response = customResource.getAttString('Response');
  }

  /**
   * Get the response of the Lambda function.
   */
  get response(): string {
    return this._response;
  }

  /**
   * Get the function.
   */
  get function(): IFunction {
    return this._function;
  }
}
