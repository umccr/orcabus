import { Construct } from 'constructs';
import { IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { aws_ec2 } from 'aws-cdk-lib';

export interface Props {
  vpc: IVpc;
}

export class SecurityGroupConstruct extends Construct {
  public static readonly ORCABUS_LAMBDA_SECURITY_GROUP: string = 'OrcaBusLambdaSecurityGroup';

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    const lambdaSecurityGroup = new SecurityGroup(this, 'LambdaSecurityGroup', {
      securityGroupName: SecurityGroupConstruct.ORCABUS_LAMBDA_SECURITY_GROUP,
      vpc: props.vpc,
      allowAllOutbound: true,
    });
    lambdaSecurityGroup.addIngressRule(lambdaSecurityGroup, aws_ec2.Port.allTraffic(), 'Allow within same SecurityGroup');
  }
}
