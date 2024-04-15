import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { aws_lambda, aws_secretsmanager, Duration, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { SRMApiGatewayConstruct } from './apigw/component';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { PostgresManagerStack } from '../../postgres_manager/deploy/postgres-manager-stack';

export interface SequenceRunManagerProps {
  securityGroups: ISecurityGroup[];
  vpc: IVpc;
  mainBus: IEventBus;
}

export class SequenceRunManagerStack extends Stack {
  private readonly secretId: string = PostgresManagerStack.formatDbSecretManagerName('sequence_run_manager');
  private readonly apiName: string = 'SequenceRunManager';  // apiNamespace `/srm/v1` is handled by Django Router
  private readonly id: string;
  private readonly props: SequenceRunManagerProps;
  private readonly baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private readonly lambdaRole: Role;

  constructor(scope: Construct, id: string, props: cdk.StackProps & SequenceRunManagerProps) {
    super(scope, id);

    this.id = id;
    this.props = props;

    this.lambdaRole = new Role(this, this.id + 'Role', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + this.id,
    });
    // FIXME it is best practise to such that we do not use AWS managed policy
    //  we should improve this at some point down the track.
    //  See https://github.com/umccr/orcabus/issues/174
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMReadOnlyAccess'),
    );

    const dbSecret = aws_secretsmanager.Secret.fromSecretNameV2(this, this.id + 'dbSecret', this.secretId);
    dbSecret.grantRead(this.lambdaRole);

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'sequence_run_manager.settings.aws',
      EVENT_BUS_NAME: this.props.mainBus.eventBusName,
      SECRET_ID: this.secretId,
    };

    this.baseLayer = new PythonLayerVersion(this, this.id + 'Layer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [this.lambdaRuntimePythonVersion],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    this.createMigrationHandler();
    this.createApiHandlerAndIntegration();
    this.createProcSqsHandler();
  }

  private createPythonFunction(name: string, props: object): PythonFunction {
    return new PythonFunction(this, this.id + name, {
      entry: path.join(__dirname, '../'),
      runtime: this.lambdaRuntimePythonVersion,
      layers: [this.baseLayer],
      environment: this.lambdaEnv,
      securityGroups: this.props.securityGroups,
      vpc: this.props.vpc,
      vpcSubnets: { subnets: this.props.vpc.privateSubnets },
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

  private createApiHandlerAndIntegration() {
    const apiFn: PythonFunction = this.createPythonFunction('Api', {
      index: 'api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    const srmApi = new SRMApiGatewayConstruct(this, this.id + 'SRMApiGatewayConstruct', this.apiName, this.region);
    const httpApi = srmApi.httpApi;

    const apiIntegration = new HttpLambdaIntegration(this.id + 'ApiIntegration', apiFn);

    new HttpRoute(this, this.id + 'HttpRoute', {
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

    this.props.mainBus.grantPutEventsTo(procSqsFn);
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
