import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { Role } from 'aws-cdk-lib/aws-iam';
import { IVpc, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../components/api-gateway';
import { HtsgetLambda } from 'htsget-lambda';

/**
 * Configurable props for the htsget stack.
 */
export type HtsgetStackProps = {
  /**
   * Props to lookup vpc.
   */
  vpcProps: VpcLookupOptions;
  /**
   * API gateway construct props.
   */
  apiGatewayCognitoProps: ApiGatewayConstructProps;
  /**
   * The buckets to configure for htsget access.
   */
  buckets: string[];
  /**
   * The role name to use.
   */
  roleName: string;
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
    const role = Role.fromRoleName(this, 'Role', props.roleName);

    new HtsgetLambda(this, 'Htsget', {
      htsgetConfig: {
        environment_override: {
          HTSGET_LOCATIONS: props.buckets.map((bucket) => {
            let regex = `^${bucket}/(?P<key>.*)$`;
            let substitution_string = '$key';
            let backend = `{ kind=S3, bucket=${bucket} }`;

            return `{ regex=${regex}, substitution_string=${substitution_string}, backend=${backend} }`;
          }),
        },
      },
      cargoLambdaFlags: ['--features', 'aws'],
      vpc: this.vpc,
      role,
      httpApi: this.apiGateway.httpApi,
      gitReference: 'htsget-lambda-v0.6.0',
      gitForceClone: false,
    });
  }
}
