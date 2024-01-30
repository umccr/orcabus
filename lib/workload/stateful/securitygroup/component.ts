import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface SecurityGroupProps {
  securityGroupName: string;
  securityGroupDescription: string;
}

export class SecurityGroupConstruct extends Construct {
  readonly computeSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: SecurityGroupProps) {
    super(scope, id);

    this.computeSecurityGroup = new ec2.SecurityGroup(this, id + 'ComputeSecurityGroup', {
      securityGroupName: props.securityGroupName,
      vpc: vpc,
      allowAllOutbound: true,
    });

    this.computeSecurityGroup.addIngressRule(
      this.computeSecurityGroup,
      ec2.Port.allTraffic(),
      props.securityGroupDescription
    );
  }
}
