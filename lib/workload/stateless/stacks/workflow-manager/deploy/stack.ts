import path from 'path';
import { Construct } from 'constructs';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { ISecurityGroup, IVpc, SecurityGroup, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { EventBus, IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import {
  aws_events_targets,
  aws_lambda,
  aws_secretsmanager,
  Duration,
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { PostgresManagerStack } from '../../../../stateful/stacks/postgres-manager/deploy/stack';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../../components/api-gateway';

export interface WorkflowManagerStackProps extends StackProps {
  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;
  mainBusName: string;
  apiGatewayCognitoProps: ApiGatewayConstructProps;
}

export class WorkflowManagerStack extends Stack {
  private props: WorkflowManagerStackProps;
  private baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private readonly lambdaRole: Role;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly vpc: IVpc;

  constructor(scope: Construct, id: string, props: WorkflowManagerStackProps) {
    super(scope, id, props);

    this.props = props;

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

    const secretId: string = PostgresManagerStack.formatDbSecretManagerName('workflow_manager');
    const dbSecret = aws_secretsmanager.Secret.fromSecretNameV2(this, 'DbSecret', secretId);
    dbSecret.grantRead(this.lambdaRole);

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'workflow_manager.settings.aws',
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
    this.createHandleServiceWrscEventHandler();
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
      memorySize: 1024,
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

  private createApiHandlerAndIntegration(props: WorkflowManagerStackProps) {
    const API_VERSION = 'v1';
    const apiFn: PythonFunction = this.createPythonFunction('Api', {
      index: 'api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    const wfmApi = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const httpApi = wfmApi.httpApi;

    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiFn);

    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.GET),
    });

    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.POST),
    });

    new HttpRoute(this, 'PatchHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.PATCH),
    });

    new HttpRoute(this, 'DeleteHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.DELETE),
    });

    // Route and permission for rerun cases where it needs to put event to mainBus
    this.mainBus.grantPutEventsTo(apiFn);
    new HttpRoute(this, 'PostRerunHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      authorizer: wfmApi.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(
        `/api/${API_VERSION}/workflowrun/{orcabusId}/rerun/{proxy+}`,
        HttpMethod.POST
      ),
    });
  }

  private createHandleServiceWrscEventHandler() {
    const procFn: PythonFunction = this.createPythonFunction('HandleServiceWrscEvent', {
      index: 'workflow_manager_proc/lambdas/handle_service_wrsc_event.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });

    this.mainBus.grantPutEventsTo(procFn);

    const eventRule = new Rule(this, 'EventRule', {
      description:
        'Rule to send WorkflowRunStateChange events to the HandleServiceWrscEvent Lambda',
      eventBus: this.mainBus,
    });

    eventRule.addTarget(new aws_events_targets.LambdaFunction(procFn));
    eventRule.addEventPattern({
      // See https://github.com/aws/aws-cdk/issues/30220
      // @ts-ignore
      source: [{ 'anything-but': 'orcabus.workflowmanager' }],
      detailType: ['WorkflowRunStateChange'],
    });
  }
}
