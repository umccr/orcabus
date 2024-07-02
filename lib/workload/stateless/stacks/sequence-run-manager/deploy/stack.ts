import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { aws_lambda, aws_secretsmanager, Duration, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ISecurityGroup, IVpc, SecurityGroup, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { EventBus, IEventBus } from 'aws-cdk-lib/aws-events';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { ApiGatewayConstruct, ApiGwLogsConfig } from '../../../../components/api-gateway';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { PostgresManagerStack } from '../../../../stateful/stacks/postgres-manager/deploy/stack';

export interface SequenceRunManagerStackProps {
  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;
  mainBusName: string;
  cognitoUserPoolIdParameterName: string;
  cognitoPortalAppClientIdParameterName: string;
  cognitoStatusPageAppClientIdParameterName: string;
  apiGwLogsConfig: ApiGwLogsConfig;
}

export class SequenceRunManagerStack extends Stack {
  private readonly baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private readonly lambdaRole: Role;
  private readonly vpc: IVpc;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;

  constructor(scope: Construct, id: string, props: cdk.StackProps & SequenceRunManagerStackProps) {
    super(scope, id, props);

    const secretId: string = PostgresManagerStack.formatDbSecretManagerName('sequence_run_manager');

    this.mainBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.mainBusName);
    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
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

    const dbSecret = aws_secretsmanager.Secret.fromSecretNameV2(this, 'DbSecret', secretId);
    dbSecret.grantRead(this.lambdaRole);

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'sequence_run_manager.settings.aws',
      EVENT_BUS_NAME: this.mainBus.eventBusName,
      SECRET_ID: secretId,
    };

    this.baseLayer = new PythonLayerVersion(this, 'BaseLayer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [this.lambdaRuntimePythonVersion],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    this.createMigrationHandler();
    this.createApiHandlerAndIntegration(props);
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

  private createApiHandlerAndIntegration(props: SequenceRunManagerStackProps) {
    const apiFn: PythonFunction = this.createPythonFunction('Api', {
      index: 'api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    const srmApi = new ApiGatewayConstruct(this, 'ApiGateway', {
      region: this.region,
      apiName: 'SequenceRunManager',
      customDomainNamePrefix: 'sequence',
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

  private createProcSqsHandler() {
    const procSqsFn = this.createPythonFunction('ProcHandler', {
      index: 'sequence_run_manager_proc/lambdas/bssh_event.py',
      handler: 'sqs_handler',
      timeout: Duration.minutes(2),
    });

    this.mainBus.grantPutEventsTo(procSqsFn);
    // this.setupEventRule(procSqsFn);  // TODO comment this out for now
  }

  // private setupEventRule(fn: aws_lambda.Function) {
  //   const eventRule = new Rule(this, this.id + 'EventRule', {
  //     ruleName: this.id + 'EventRule',
  //     description: 'Rule to send {event_type.value} events to the {handler.function_name} Lambda',
  //     eventBus: this.props.mainBus,
  //   });
  //
  //   eventRule.addTarget(new aws_events_targets.LambdaFunction(fn));
  //   eventRule.addEventPattern({
  //     source: ['ORCHESTRATOR'], // FIXME complete source to destination event mapping
  //     detailType: ['SequenceRunStateChange'],
  //   });
  // }
}
