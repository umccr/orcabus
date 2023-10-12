import { aws_ec2 as ec2, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { FargateService } from 'aws-cdk-lib/aws-ecs';
import {
  CfnLoadBalancer,
  NetworkLoadBalancer,
  Protocol,
} from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { ISecurityGroup, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';

export type EdgeDbLoadBalancerProtocolPassthroughProps = {
  // the port that the load balancer will listen on for TCP pass through work - this is the normal
  // way for interacting with EdgeDb (i.e. edgedb:// protocol)
  tcpPassthroughPort: number;
};

type Props = EdgeDbLoadBalancerProtocolPassthroughProps & {
  // the VPC that the load balancer back side will live in
  vpc: ec2.IVpc;

  // the service we will balance to
  service: FargateService;

  // the service port we will balance to
  servicePort: number;

  // the security group we need to place the NLB in to access the service
  serviceSecurityGroup: ISecurityGroup;
};

/**
 * A network load balancer that can sit in front of a Fargate EdgeDb service
 * and provides direct protocol access.
 * https://www.edgedb.com/docs/reference/protocol/index
 */
export class EdgeDbLoadBalancerProtocolConstruct extends Construct {
  private readonly _lb: NetworkLoadBalancer;

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    this._lb = new NetworkLoadBalancer(this, 'LoadBalancer', {
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      // the edgedb can only be accessed internally for protocol access
      internetFacing: false,
    });

    const nlbSecurityGroup = new SecurityGroup(this, 'LbProtocolSecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description:
        'Security group of the NLB (EdgeDb protocol) allowing egress to the EdgeDb service on its port',
    });
    nlbSecurityGroup.addEgressRule(props.serviceSecurityGroup, ec2.Port.tcp(props.servicePort));

    // NLBs now have security groups - but not in CDK yet - this is a workaround - Aug 2023
    // review at some point and replace this with proper CDK usage
    const cfnLb = this._lb.node.defaultChild as CfnLoadBalancer;
    cfnLb.addPropertyOverride('SecurityGroups', [
      nlbSecurityGroup.securityGroupId,
      props.serviceSecurityGroup.securityGroupId,
    ]);

    // note for protocol access the NLB does not do *any* TLS handling itself
    // it just passes connection through directly
    const tcpListener = this._lb.addListener('TcpListener', {
      port: props.tcpPassthroughPort,
      protocol: Protocol.TCP,
    });

    const tg = tcpListener.addTargets('TcpTargetGroup', {
      port: props.servicePort,
      protocol: Protocol.TCP,
      targets: [props.service],
      // the assumption is our code/db will handle reasonably quick shutdown of the
      // service and just abort transactions etc (I mean, that's what a database is for)
      deregistrationDelay: Duration.seconds(15),
    });

    // whilst all the IPs hitting us will be internal IPs - we prefer to be logging the actual IPs
    // of the client rather than the NLB interface IPs
    tg.setAttribute('preserve_client_ip.enabled', 'true');

    tg.configureHealthCheck({
      enabled: true,
      interval: Duration.seconds(10),
      timeout: Duration.seconds(5),
      healthyThresholdCount: 2,
      unhealthyThresholdCount: 2,
    });
  }

  public get loadBalancer(): NetworkLoadBalancer {
    return this._lb;
  }

  public get dnsName(): string {
    return this._lb.loadBalancerDnsName;
  }
}
