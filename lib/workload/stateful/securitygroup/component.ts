import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface SecurityGroupProps {
  securityGroupName: string;
  securityGroupDescription: string;
}

export class SecurityGroupConstruct extends Construct {
  readonly lambdaSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: SecurityGroupProps) {
    super(scope, id);

    this.lambdaSecurityGroup = new ec2.SecurityGroup(this, id + 'LambdaSecurityGroup', {
      securityGroupName: props.securityGroupName,
      vpc: vpc,
      allowAllOutbound: true,
    });
    this.lambdaSecurityGroup.addIngressRule(
      this.lambdaSecurityGroup,
      ec2.Port.allTraffic(),
      props.securityGroupDescription
    );
  }
}
