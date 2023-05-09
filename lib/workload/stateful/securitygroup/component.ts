import { Construct } from 'constructs';
import { IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { aws_ec2 } from 'aws-cdk-lib';

export interface SecurityGroupProps {
  securityGroupName: string,
  securityGroupDescription: string,
}

export class SecurityGroupConstruct extends Construct {

  constructor(scope: Construct, id: string, vpc: IVpc, props: SecurityGroupProps) {
    super(scope, id);

    const lambdaSecurityGroup = new SecurityGroup(this, id + 'LambdaSecurityGroup', {
      securityGroupName: props.securityGroupName,
      vpc: vpc,
      allowAllOutbound: true,
    });
    lambdaSecurityGroup.addIngressRule(lambdaSecurityGroup, aws_ec2.Port.allTraffic(), props.securityGroupDescription);
  }
}
