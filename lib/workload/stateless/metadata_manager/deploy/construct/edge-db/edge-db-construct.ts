import { aws_ec2 as ec2, aws_secretsmanager as secretsmanager } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EdgeDbServiceConstruct, EdgeDbServicePassthroughProps } from './edge-db-service-construct';
import {
  EdgeDbLoadBalancerProtocolConstruct,
  EdgeDbLoadBalancerProtocolPassthroughProps,
} from './edge-db-load-balancer-protocol-construct';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { ISecurityGroup } from 'aws-cdk-lib/aws-ec2';

export interface EdgeDbProps {
  // a prefix that is used for constructing AWS secrets for edgedb
  secretsPrefix: string;

  // purely for information/descriptive purposes - the friendly short name of
  // the RDS instance we are wrapping
  rdsDatabaseDisplayName: string;

  // the underlying network infrastructure that has already
  // been set up and that we will be installing into
  vpc: ec2.IVpc;

  // the configuration of the fargate service that is edge db itself
  edgeDbService: EdgeDbServicePassthroughProps;

  // the configuration of the internal network load balancer that provides EdgeDb protocol access
  edgeDbLoadBalancerProtocol: EdgeDbLoadBalancerProtocolPassthroughProps;
}

export interface EdgeDbConfigurationProps {
  EDGEDB_HOST: string;
  EDGEDB_PORT: string;
  EDGEDB_USER: string;
  EDGEDB_DATABASE: string;
}

/**
 * A construct wrapping an installation of EdgeDb as a service (assuming
 * an existing RDS postgres).
 */
export class EdgeDbConstruct extends Construct {
  private readonly _edgeDbPasswordSecret: ISecret;
  private readonly _edgeDbSecurityGroup: ISecurityGroup;

  private readonly host: string;
  private readonly port: string;
  private readonly user: string;
  private readonly dbName: string;

  constructor(scope: Construct, id: string, props: EdgeDbProps) {
    super(scope, id);

    this.user = props.edgeDbService.superUser;
    this.dbName = props.edgeDbService.databaseName;
    this.port = `${props.edgeDbLoadBalancerProtocol.tcpPassthroughPort ?? 5656}`;

    // create a new secret for our edge db database with an autogenerated password
    this._edgeDbPasswordSecret = new secretsmanager.Secret(this, 'EdgeDbSecret', {
      description: `For database ${props.rdsDatabaseDisplayName} - secret containing EdgeDb super user password`,
      secretName: `${props.secretsPrefix}EdgeDb`,
      generateSecretString: {
        excludePunctuation: true,
      },
    });

    const edgeDbService = new EdgeDbServiceConstruct(this, 'EdgeDbService', {
      ...props.edgeDbService,
      vpc: props.vpc,
      superUserSecret: this._edgeDbPasswordSecret,
    });

    this._edgeDbSecurityGroup = edgeDbService.securityGroup;

    const edgeDbLoadBalancer = new EdgeDbLoadBalancerProtocolConstruct(
      this,
      'EdgeDbLoadBalancerProtocol',
      {
        vpc: props.vpc,
        service: edgeDbService.service,
        servicePort: edgeDbService.servicePort,
        serviceSecurityGroup: edgeDbService.securityGroup,
        ...props.edgeDbLoadBalancerProtocol,
      }
    );

    this.host = edgeDbLoadBalancer.dnsName;
  }

  public get edgeDbConnectionVariable(): EdgeDbConfigurationProps {
    return {
      EDGEDB_HOST: this.host,
      EDGEDB_PORT: this.port,
      EDGEDB_USER: this.user,
      EDGEDB_DATABASE: this.dbName,
    };
  }

  public get passwordSecret(): ISecret {
    return this._edgeDbPasswordSecret;
  }

  public get securityGroup(): ISecurityGroup {
    return this._edgeDbSecurityGroup;
  }
}
