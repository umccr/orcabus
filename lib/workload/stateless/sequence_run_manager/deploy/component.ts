import path from 'path';
import { Construct } from 'constructs';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { aws_lambda, aws_secretsmanager, Stack } from 'aws-cdk-lib';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey, IHttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';

export interface SequenceRunManagerProps {
  securityGroups: ISecurityGroup[];
  vpc: IVpc;
  mainBus: IEventBus;
  httpApi: IHttpApi;
}

export class SequenceRunManagerStack extends Stack {
  // Follow by naming convention. See https://github.com/umccr/orcabus/pull/149
  private readonly secretId: string = 'orcabus/sequence_run_manager/rdsLoginCredential';
  private readonly apiNamespace: string = '/srm/v1';
  private readonly id: string;
  private readonly props: SequenceRunManagerProps;
  private readonly baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private readonly lambdaRole: Role;

  constructor(scope: Construct, id: string, props: SequenceRunManagerProps) {
    super(scope, id);

    this.id = id;
    this.props = props;

    this.lambdaRole = new Role(this, this.id + 'Role', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + this.id,
    });
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
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
    });

    this.createMigrationHandler();
    this.createApiHandler();
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
      ...props,
    });
  }

  private createMigrationHandler() {
    this.createPythonFunction('Migration', {
      index: 'migrate.py',
      handler: 'handler',
    });
  }

  private createApiHandler() {
    const apiFn = this.createPythonFunction('Api', {
      index: 'api.py',
      handler: 'handler',
    });

    const apiIntegration = new HttpLambdaIntegration(this.id + 'ApiIntegration', apiFn);
    new HttpRoute(this, 'OrcaBusSRMHttpRoute', {
      httpApi: this.props.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(this.apiNamespace + '/{proxy+}', HttpMethod.ANY),
    });
  }

  private createProcSqsHandler() {
    const procSqsFn = this.createPythonFunction('ProcHandler', {
      index: 'sequence_run_manager_proc/lambdas/bssh_event.py',
      handler: 'sqs_handler',
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
