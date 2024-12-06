import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { Role } from 'aws-cdk-lib/aws-iam';
import { IVpc, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../components/api-gateway';
import path from 'path';
import { HtsgetLambdaConstruct } from 'htsget-lambda';

/**
 * Configurable props for the htsget stack.
 */
export type HtsgetStackConfigurableProps = {
  /**
   * Props to lookup vpc.
   */
  vpcProps: VpcLookupOptions;
  /**
   * API gateway construct props.
   */
  apiGatewayCognitoProps: ApiGatewayConstructProps;
};

/**
 * Props for the data migrate stack.
 */
export type HtsgetStackProps = HtsgetStackConfigurableProps & {
  /**
   * The role to use.
   */
  role: Role;
};

/**
 * Deploys htsget-rs with access to filemanager data.
 */
export class HtsgetStack extends Stack {
  private readonly vpc: IVpc;
  private readonly apiGateway: ApiGatewayConstruct;

  constructor(scope: Construct, id: string, props: StackProps & HtsgetStackProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);

    const configPath = path.join(__dirname, 'deploy.toml');
    new HtsgetLambdaConstruct(this, 'Htsget', {
      config: configPath,
      vpc: this.vpc,
      role: props.role,
      httpApi: this.apiGateway.httpApi,
    });
  }
}
