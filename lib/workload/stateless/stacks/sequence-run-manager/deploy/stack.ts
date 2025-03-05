import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { aws_lambda, aws_secretsmanager, Duration, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ISecurityGroup, IVpc, SecurityGroup, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { EventBus, EventField, IEventBus, Rule, RuleTargetInput } from 'aws-cdk-lib/aws-events';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { LambdaFunction, SnsTopic } from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  HttpMethod,
  HttpNoneAuthorizer,
  HttpRoute,
  HttpRouteKey,
} from 'aws-cdk-lib/aws-apigatewayv2';
import {
  ManagedPolicy,
  PolicyStatement,
  Role,
  ServicePrincipal,
  Effect,
} from 'aws-cdk-lib/aws-iam';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../../components/api-gateway';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { PostgresManagerStack } from '../../../../stateful/stacks/postgres-manager/deploy/stack';

export interface SequenceRunManagerStackProps {
  lambdaSecurityGroupName: string;
  vpcProps: VpcLookupOptions;
  mainBusName: string;
  apiGatewayCognitoProps: ApiGatewayConstructProps;
  bsshTokenSecretName: string;
  slackTopicName: string;
  orcabusUIBaseUrl: string;
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
      ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaSQSQueueExecutionRole')
    );
    this.lambdaRole.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMReadOnlyAccess')
    );

    const dbSecret = aws_secretsmanager.Secret.fromSecretNameV2(this, 'DbSecret', secretId);
    dbSecret.grantRead(this.lambdaRole);

    const bsshTokenSecret = aws_secretsmanager.Secret.fromSecretNameV2(
      this,
      'BsshTokenSecret',
      props.bsshTokenSecretName
    );
    bsshTokenSecret.grantRead(this.lambdaRole);

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'sequence_run_manager.settings.aws',
      EVENT_BUS_NAME: this.mainBus.eventBusName,
      SECRET_ID: secretId,
      BASESPACE_ACCESS_TOKEN_SECRET_ID: props.bsshTokenSecretName,
    };

    this.baseLayer = new PythonLayerVersion(this, 'BaseLayer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [this.lambdaRuntimePythonVersion],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    this.createMigrationHandler();
    this.createApiHandlerAndIntegration(props);
    this.createProcSqsHandler();
    this.createSlackNotificationHandler(props.slackTopicName, props.orcabusUIBaseUrl);
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

    const srmApi = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const httpApi = srmApi.httpApi;

    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiFn);

    // Routes for API schemas
    new HttpRoute(this, 'GetSchemaHttpRoute', {
      httpApi: srmApi.httpApi,
      integration: apiIntegration,
      authorizer: new HttpNoneAuthorizer(), // No auth needed for schema
      routeKey: HttpRouteKey.with(`/schema/{PROXY+}`, HttpMethod.GET),
    });

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
  }

  private createProcSqsHandler() {
    /**
     * For `reservedConcurrentExecutions 1` setting, we are practising Singleton Lambda pattern here.
     * See https://umccr.slack.com/archives/C03ABJTSN7J/p1721685789381979 for context.
     * SRM processing is low volume event with time delay friendly (so to speak upto some minutes).
     * We also make SQS to complimenting delayed queue. See https://github.com/umccr/infrastructure/pull/469
     */
    const procSqsFn = this.createPythonFunction('ProcHandler', {
      index: 'sequence_run_manager_proc/lambdas/bssh_event.py',
      handler: 'event_handler',
      timeout: Duration.minutes(2),
      memorySize: 512,
      reservedConcurrentExecutions: 1,
    });

    this.mainBus.grantPutEventsTo(procSqsFn);
    this.setupEventRule(procSqsFn); // TODO comment this out for now
  }

  private setupEventRule(fn: aws_lambda.Function) {
    /**
     * For sequence run manager, we are using orcabus events ( source from BSSH ENS event pipe) to trigger the lambda function.
     * event rule to filter the events that we are interested in.
     * event pattern: see below
     * process lambda will record the event to the database, and emit the 'SequenceRunStateChange' event to the event bus.
     *
     */
    const eventRule = new Rule(this, this.stackName + 'EventRule', {
      ruleName: this.stackName + 'EventRule',
      description: 'Rule to send BSSH ENS events to the SRM ProcHandler Lambda',
      eventBus: this.mainBus,
    });
    eventRule.addEventPattern({
      detailType: ['Event from aws:sqs'],
      detail: {
        'ica-event': {
          // mandatory fields (gdsFolderPath, gdsVolumeName(starts with bssh), instrumentRunId, dateModified)
          gdsFolderPath: [{ exists: true }],
          gdsVolumeName: [{ prefix: 'bssh' }],
          instrumentRunId: [{ exists: true }],
          dateModified: [{ exists: true }],

          // optional fields (flowcell barcode, sample sheet name, reagent barcode, ica project id, api url, name)
          acl: [{ prefix: 'wid:' }, { prefix: 'tid:' }],
          id: [{ exists: true }],
          status: [{ exists: true }],
        },
      },
    });

    eventRule.addTarget(new LambdaFunction(fn));
  }

  private createSlackNotificationHandler(topicName: string, orcabusUIBaseUrl: string) {
    /**
     * subscribe to the 'SequenceRunStateChange' event, and send the slack notification toptic when the failed event is triggered.
     */
    const slackTopicArn = 'arn:aws:sns:' + this.region + ':' + this.account + ':' + topicName;
    const topic: Topic = Topic.fromTopicArn(this, 'SlackTopic', slackTopicArn) as Topic;

    /**
     * TODO CDK can't modify the resource policy as it is an "imported" resource (manually created).
     * Need to add a resource policy to allow EventBridge to publish to this SNS topic.
     * manually added resource policy:
     * {
      "Sid": "AWSEvents_OrcaBusBeta-SequenceRunManagerStackSlackNotificationRule_Id85755e27-3dd5-408e-9091-9cbc7315db7e",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:ap-southeast-2:843407916570:AwsChatBotTopic-alerts"
      }
     */
    topic.addToResourcePolicy(
      new PolicyStatement({
        principals: [new ServicePrincipal('events.amazonaws.com')],
        actions: ['SNS:Publish'],
        resources: [topic.topicArn],
        effect: Effect.ALLOW,
      })
    );

    const eventRule = new Rule(this, this.stackName + 'SlackNotificationRule', {
      ruleName: this.stackName + 'SlackNotificationRule',
      description: 'Rule to send SequenceRunStateChange events (failed) to the SlackTopic',
      eventBus: this.mainBus,
    });
    eventRule.addEventPattern({
      source: ['orcabus.sequencerunmanager'],
      detailType: ['SequenceRunStateChange'],
      detail: {
        status: ['FAILED'],
        id: [{ exists: true }],
        instrumentRunId: [{ exists: true }],
        startTime: [{ exists: true }],
        endTime: [{ exists: true }],
      },
    });

    eventRule.addTarget(
      new SnsTopic(topic, {
        message: RuleTargetInput.fromObject({
          // custome chat bot message format here: https://docs.aws.amazon.com/chatbot/latest/adminguide/custom-notifs.html
          version: '1.0',
          source: 'custom',
          content: {
            textType: 'client-markdown',
            title:
              ':bell: Sequence Run Status Alert | RUN ID: ' + EventField.fromPath('$.detail.id'),
            description: [
              '*Status:* ' + EventField.fromPath('$.detail.status'),
              '',
              ':clipboard: Run Details',
              '',
              '*Sequence ID:* `' + EventField.fromPath('$.detail.id') + '`',
              '*Instrument Run ID:* `' + EventField.fromPath('$.detail.instrumentRunId') + '`',
              '*Start:* `' + EventField.fromPath('$.detail.startTime') + '`',
              '*End:* `' + EventField.fromPath('$.detail.endTime') + '`',
              '',
              ':microscope: <' +
                orcabusUIBaseUrl +
                '/runs/sequence/' +
                EventField.fromPath('$.detail.id') +
                '|View in Orcabus UI>',
              '',
              '---',
              '_For support, please contact the orcabus platform team_',
            ].join('\n'),
          },
        }),
      })
    );
  }
}
