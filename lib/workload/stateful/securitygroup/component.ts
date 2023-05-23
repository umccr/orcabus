import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface SecurityGroupProps {
  securityGroupName: string;
  securityGroupDescription: string;
}
export interface SecurityGroupConstructProps extends SecurityGroupProps {
  dbSecurityGroup: ec2.SecurityGroup;
}
export class SecurityGroupConstruct extends Construct {
  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: SecurityGroupConstructProps) {
    super(scope, id);

    const lambdaSecurityGroup = new ec2.SecurityGroup(this, id + 'LambdaSecurityGroup', {
      securityGroupName: props.securityGroupName,
      vpc: vpc,
      allowAllOutbound: true,
    });
    lambdaSecurityGroup.addIngressRule(
      lambdaSecurityGroup,
      ec2.Port.allTraffic(),
      props.securityGroupDescription
    );

    // Adding lambda ingress rule for database SG
    props.dbSecurityGroup.addIngressRule(
      lambdaSecurityGroup,
      ec2.Port.tcp(3306),
      'allow lambda SecurityGroup'
    );
  }
}
