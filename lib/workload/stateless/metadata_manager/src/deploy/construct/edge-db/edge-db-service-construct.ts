import {
  aws_ec2 as ec2,
  aws_ecs as ecs,
  aws_iam as iam,
  aws_logs as logs,
  Duration,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
  CpuArchitecture,
  FargateService,
  FargateTaskDefinition,
  LogDrivers,
  OperatingSystemFamily,
  Protocol,
} from 'aws-cdk-lib/aws-ecs';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { ISecurityGroup, IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';

/**
 * A collection of props that are set in the highest level EdgeDb construct
 * but which are then passed through to this construct.
 */
export type EdgeDbServicePassthroughProps = {
  // the DSN of the Postgres db it will use for its store (the DSN must include base db user/pw)
  postgresDsn: string;

  // the security group of the Postgres database
  postgresSecurityGroup: ISecurityGroup;

  // the settings for containers of the service
  desiredCount: number;
  cpu: number;
  memory: number;

  // the edge db superuser name
  superUser: string;

  // edge db version string for the docker image used for edge db e.g. "2.3"
  edgeDbVersion: string;

  // if present and true, enable the EdgeDb feature flag to switch on the UI
  // NOTE there are other settings that need to be true for the UI to actually be on the internet!
  enableUiFeatureFlag?: boolean;
};

/**
 * An augmenting of the high level pass through props with other
 * settings we have created on the way.
 */
type EdgeDbServiceProps = EdgeDbServicePassthroughProps & {
  // the VPC that the service will live in
  vpc: ec2.IVpc;

  // the secret holding the EdgeDb superuser password
  superUserSecret: ISecret;
};

/**
 * The EdgeDb service is a Fargate task cluster running the EdgeDb
 * Docker image and pointing to an existing Postgres database.
 *
 * The service is set up to use self-signed certs assuming
 * - network load balancer will sit in front of it and that NLB will deal with TLS termination
 * - a client will connect and the client will ignore certs
 */
export class EdgeDbServiceConstruct extends Construct {
  // this construct is predicated on using the default EdgeDb port
  // so if you want to change this then you'll have to add some extra PORT settings in various places
  private readonly EDGE_DB_PORT = 5656;

  private readonly _service: FargateService;
  private readonly _securityGroup: SecurityGroup;

  constructor(scope: Construct, id: string, props: EdgeDbServiceProps) {
    super(scope, id);

    const cluster = new ecs.Cluster(this, 'Cluster', {
      vpc: props.vpc,
    });

    const executionRole = new iam.Role(this, 'ExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
      ],
    });

    const clusterLogGroup = new logs.LogGroup(this, 'ServiceLog', {
      retention: logs.RetentionDays.ONE_WEEK,
    });

    // we do the task definition by hand as we have some specialised settings (ARM64 etc)
    const taskDefinition = new FargateTaskDefinition(this, 'TaskDefinition', {
      runtimePlatform: {
        operatingSystemFamily: OperatingSystemFamily.LINUX,
        cpuArchitecture: CpuArchitecture.ARM64,
      },
      memoryLimitMiB: props.memory,
      cpu: props.cpu,
      executionRole: executionRole,
      family: 'edge-db-service-family',
    });

    const containerName = 'edge-db';

    const env: { [k: string]: string } = {
      EDGEDB_DOCKER_LOG_LEVEL: 'debug',
      // the DSN (including postgres user/pw) pointing to the base database
      EDGEDB_SERVER_BACKEND_DSN: props.postgresDsn,
      // we allow the superuser name to be set
      EDGEDB_SERVER_USER: props.superUser,
      // we don't do edgedb certs at all - rely on self-signed always
      // when putting a TLS terminated network load balancer in front of this - we can
      // use a self-signed cert as the internal target TLS
      // NLBs are comfortable using self-signed certs purely for traffic encryption
      // https://kevin.burke.dev/kevin/aws-alb-validation-tls-reply/
      // that way we can avoid needing to manage custom certs/cas
      EDGEDB_SERVER_GENERATE_SELF_SIGNED_CERT: '1',
      // DO NOT ENABLE
      // EDGEDB_SERVER_DEFAULT_AUTH_METHOD: "Trust"
    };

    const secrets: { [k: string]: ecs.Secret } = {
      // CDK is smart enough to grant permissions to read these secrets to the execution role
      EDGEDB_SERVER_PASSWORD: ecs.Secret.fromSecretsManager(props.superUserSecret),
    };

    if (props.enableUiFeatureFlag) env.EDGEDB_SERVER_ADMIN_UI = 'enabled';

    taskDefinition.addContainer(containerName, {
      // https://hub.docker.com/r/edgedb/edgedb/tags
      image: ecs.ContainerImage.fromRegistry(`edgedb/edgedb:${props.edgeDbVersion}`),
      environment: env,
      secrets: secrets,
      logging: LogDrivers.awsLogs({
        streamPrefix: 'edge-db',
        logGroup: clusterLogGroup,
      }),
      portMappings: [
        {
          containerPort: this.EDGE_DB_PORT,
          protocol: Protocol.TCP,
        },
      ],
    });

    // the membership security group is a group that defines who is allowed to connect to the EdgeDb
    this._securityGroup = this.createMembershipSecurityGroup(props.vpc);

    this._service = new FargateService(this, 'Service', {
      // even in dev mode we never want to assign public ips to the fargate service...
      // we *ALWAYS* want to access via network load balancer - and that NLB can either be internal or external
      assignPublicIp: false,
      cluster: cluster,
      desiredCount: props.desiredCount,
      taskDefinition: taskDefinition,
      vpcSubnets: {
        // we need egress in order to fetch images?? if we setup with private link maybe avoid? one to investigate?
        // again - we are *always* putting the service containers in private - it is our network load balancer
        // that can live in public/private
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      // in practice an EdgeDb startup (from logs) went (timestamps)
      // from 10:03:17
      // to   10:03:26
      // i.e. 10 seconds - so allocating 30 seconds to be safe
      healthCheckGracePeriod: Duration.seconds(30),
      securityGroups: [
        // a security group that allows the EdgeDb to reach the world
        new ec2.SecurityGroup(this, 'EgressSecurityGroup', {
          vpc: props.vpc,
          allowAllOutbound: true,
          description:
            'Security group that allows the EdgeDb service to reach out over the network',
        }),
        // a security group allowing access from the internal IPs (needed for the NLBs)
        this._securityGroup,
        // a security group that the service needs that gives it the "ability to connect to RDS"
        props.postgresSecurityGroup,
      ],
    });
  }

  private createMembershipSecurityGroup(vpc: IVpc) {
    const sg = new SecurityGroup(this, 'MembershipSecurityGroup', {
      vpc: vpc,
      // databases don't use outbound traffic via a security group unless you are getting them to reach
      // out via a stored procedure or something
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description:
        'Security group for resources that can communicate to the contained EdgeDb service',
    });
    // the ingress is self-referential - only allowing traffic from itself to the edge port
    sg.addIngressRule(sg, ec2.Port.tcp(this.EDGE_DB_PORT));
    // the egress is also self-referential - and allowing outbouynd traffic to anyone in the same
    // group (the all-traffic is safe because the other resources are responsible for setting their
    // ingress rules to a set port0
    sg.addEgressRule(sg, ec2.Port.allTraffic());
    return sg;
  }

  public get service(): FargateService {
    return this._service;
  }

  public get securityGroup(): ISecurityGroup {
    return this._securityGroup;
  }

  public get servicePort(): number {
    return this.EDGE_DB_PORT;
  }
}
