// FIXME complete the implementation

import path from 'path';
import { Construct } from 'constructs';
import { Architecture, ILayerVersion } from 'aws-cdk-lib/aws-lambda';
import { ISecurityGroup, IVpc, SecurityGroup, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { EventBus, IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { aws_events_targets, aws_lambda, aws_secretsmanager, Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { CorsHttpMethod, HttpApi, HttpMethod, HttpRoute, HttpRouteKey, HttpStage } from 'aws-cdk-lib/aws-apigatewayv2';
import { PostgresManagerStack } from '../../../lib/workload/stateless/stacks/postgres-manager/deploy/stack';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { ApiGatewayConstruct } from '../../../lib/workload/components/api-gateway';

export interface ProjectNameStackProps { // FIXME change prop interface name
  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;
  mainBusName: string;
  cognitoUserPoolIdParameterName: string;
  cognitoPortalAppClientIdParameterName: string;
  cognitoStatusPageAppClientIdParameterName: string;
}

export class ProjectNameStack extends Stack {  // FIXME change construct name
  private props: ProjectNameStackProps;
  private baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private readonly lambdaRole: Role;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly vpc: IVpc;

  constructor(scope: Construct, id: string, props: StackProps & ProjectNameStackProps) {
    super(scope, id, props);

    this.props = props;

    this.mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.mainBusName);
    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc,
    );

    this.lambdaRole = new Role(this, 'LambdaRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + id,
    });
    // FIXME it is best practise to such that we do not use AWS managed policy
    //  we should improve this at some point down the track.
    //  See https://github.com/umccr/orcabus/issues/174
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole')
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMReadOnlyAccess')
    );

    const secretId: string = PostgresManagerStack.formatDbSecretManagerName('hello_manager');
    const dbSecret = aws_secretsmanager.Secret.fromSecretNameV2(this, 'DbSecret', secretId);
    dbSecret.grantRead(this.lambdaRole);

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: '{{ProjectName}}.settings.aws', // FIXME project name
      EVENT_BUS_NAME: this.mainBus.eventBusName,
    };

    this.baseLayer = new PythonLayerVersion(this, 'BaseLayer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [this.lambdaRuntimePythonVersion],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    this.createMigrationHandler();
    this.createApiHandlerAndIntegration(props);
    this.createProcHandler();
    this.createProcSqsHandler();
  }

  private createPythonFunction(name: string, props: object): PythonFunction {
    return new PythonFunction(this, name, {
      entry: path.join(__dirname, '../'),
      runtime: this.lambdaRuntimePythonVersion,
      layers: [this.baseLayer],
      environment: this.lambdaEnv,
      securityGroups: [this.lambdaSG],
      vpc: this.vpc,
      vpcSubnets: { subnets: this.vpc.privateSubnets },
      role: this.lambdaRole,
      architecture: Architecture.ARM_64,
      ...props,
    });
  }

  private createMigrationHandler() {
    this.createPythonFunction('Migration', {
      index: 'migrate.py',
      handler: 'handler',
      timeout: Duration.minutes(2),
    });
  }

  private createApiHandlerAndIntegration(props: ProjectNameStackProps) {
    const apiFn: PythonFunction = this.createPythonFunction('Api', {
      index: 'api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    const srmApi = new ApiGatewayConstruct(this, 'ApiGateway', {
      region: this.region,
      apiName: 'SequenceRunManager',
      ...props,
    });
    const httpApi = srmApi.httpApi;

    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiFn);

    new HttpRoute(this, 'HttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.ANY),
    });
  }

  private createProcHandler() {
    const procFn: PythonFunction = this.createPythonFunction('Proc', {
      index: '{{project_name}}_proc/lambdas/hello_proc.py',  // FIXME update appropriate path to Lambda entry point
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    this.mainBus.grantPutEventsTo(procFn);
    this.setupEventRule(procFn);
  }

  private createProcSqsHandler() {
    const procSqsFn: PythonFunction = this.createPythonFunction('ProcSqs', {
      index: '{{project_name}}_proc/lambdas/hello_proc.py',  // FIXME update appropriate path to Lambda entry point
      handler: 'sqs_handler',
      timeout: Duration.seconds(28),
    });

    // this.mainBus.grantPutEventsTo(procSqsFn); // FIXME remove this if no use
    // this.setupEventRule(procSqsFn); // FIXME remove this if no use
  }

  private setupEventRule(fn: aws_lambda.Function) {
    const eventRule = new Rule(this, 'EventRule', {
      ruleName: 'EventRule',
      description: 'Rule to send {event_type.value} events to the {handler.function_name} Lambda',
      eventBus: this.mainBus,
    });

    eventRule.addTarget(new aws_events_targets.LambdaFunction(fn));
    eventRule.addEventPattern({
      source: ['orcabus.foo'], // FIXME complete source to destination event mapping
      detailType: ['FooRunStateChange'],
    });
  }
}
