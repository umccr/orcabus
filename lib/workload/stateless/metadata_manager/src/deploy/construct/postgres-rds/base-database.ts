import { Construct } from 'constructs';
import { ISecurityGroup, IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { aws_ec2 as ec2 } from 'aws-cdk-lib';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';

/**
 * An abstract concept that helps us wrap the CDK concepts of
 * a RDS instance v a RDS cluster v RDS serverless - which
 * are all _basically_ the same from our perspective but are
 * different enough types in CDK that it is annoying.
 */
export abstract class BaseDatabase extends Construct {
  protected constructor(scope: Construct, id: string) {
    super(scope, id);
  }

  protected createMonitoringRole() {
    const monitoringRole = new Role(this, 'DatabaseMonitoringRole', {
      assumedBy: new ServicePrincipal('monitoring.rds.amazonaws.com'),
    });
    monitoringRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonRDSEnhancedMonitoringRole')
    );
    return monitoringRole;
  }

  protected createMembershipSecurityGroup(vpc: IVpc) {
    return new SecurityGroup(this, 'MembershipSecurityGroup', {
      vpc: vpc,
      // databases don't use outbound traffic via a security group unless you are getting them to reach
      // out via a stored procedure or something
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description:
        'Security group for resources that can communicate to the contained RDS instance',
    });
  }

  /**
   * To the security group apply ingress rules giving access to the database
   * (either from the public or from the security group itself)
   *
   * @param securityGroup
   * @param databasePort
   * @param makePubliclyReachable
   * @protected
   */
  protected applySecurityGroupRules(
    securityGroup: ISecurityGroup,
    databasePort: number,
    makePubliclyReachable?: boolean
  ) {
    if (makePubliclyReachable) {
      // we allow access from all the internet to the default db port
      securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(databasePort));
    } else {
      // the db security group can only be connected to on the default db port and only from things ALSO IN THE SAME SECURITY GROUP
      securityGroup.addIngressRule(securityGroup, ec2.Port.tcp(databasePort));
    }
    // our membership security group allows outgoing access to things in the SAME SECURITY GROUP
    // (we use allTraffic safely for egress here - as those other services will be responsible
    // for protected their incoming ports with their own ingress rules)
    securityGroup.addEgressRule(securityGroup, ec2.Port.allTraffic());
  }

  public abstract get dsnWithTokens(): string;

  public abstract get dsnNoPassword(): string;

  public abstract get hostname(): string;

  public abstract get port(): number;

  public abstract get securityGroup(): ISecurityGroup;
}
