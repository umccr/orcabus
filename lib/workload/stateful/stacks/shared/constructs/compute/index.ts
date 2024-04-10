import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface ComputeConfig {
  /**
   * The security group name for the shared security group
   */
  securityGroupName: string;
}

/**
 * Any resources that could be shared among compute resources
 */
export class ComputeConstruct extends Construct {
  readonly securityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: ComputeConfig) {
    super(scope, id);

    this.securityGroup = new ec2.SecurityGroup(this, 'SecurityGroup', {
      securityGroupName: props.securityGroupName,
      vpc: vpc,
      allowAllOutbound: true,
    });

    this.securityGroup.addIngressRule(
      this.securityGroup,
      ec2.Port.allTraffic(),
      'allow connection within the same SecurityGroup'
    );
  }
}
