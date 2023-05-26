// FIXME complete the implementation

import path from 'path';
import { Construct } from 'constructs';
import { ILayerVersion } from 'aws-cdk-lib/aws-lambda';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { aws_events_targets, aws_lambda } from 'aws-cdk-lib';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';

export interface ProjectNameProps { // FIXME change prop interface name
  layers: ILayerVersion[];
  securityGroups: ISecurityGroup[];
  vpc: IVpc;
  mainBus: IEventBus;
  functionName: string;
  lambdaRuntimePythonVersion: aws_lambda.Runtime;
}

export class ProjectNameConstruct extends Construct {  // FIXME change construct name
  private scope: Construct;
  private readonly id: string;
  private props: ProjectNameProps;
  private baseLayer: PythonLayerVersion;
  private readonly lambdaEnv;

  constructor(scope: Construct, id: string, props: ProjectNameProps) {
    super(scope, id);

    this.scope = scope;
    this.id = id;
    this.props = props;

    this.lambdaEnv = {
      DJANGO_SETTINGS_MODULE: '{{ProjectName}}.settings.aws', // FIXME project name
      EVENT_BUS_NAME: this.props.mainBus.eventBusName,
    };

    this.createLambdaLayer();
    this.createMigrationHandler();
    this.createProcHandler();
    this.createProcSqsHandler();
  }

  private createLambdaLayer() {
    this.baseLayer = new PythonLayerVersion(this, this.id + 'Layer', {
      entry: path.join(__dirname, 'src/'),
    });
  }

  private createMigrationHandler() {
    new PythonFunction(this, this.id + 'Migration', {
      entry: path.join(__dirname, 'src/'),
      runtime: this.props.lambdaRuntimePythonVersion,
      layers: [this.baseLayer],
      index: 'migrate.py',
      handler: 'handler',
      environment: this.lambdaEnv,
    });
  }

  private createProcHandler() {
    const procFn = new PythonFunction(this, this.id + 'ProcHandler', {
      entry: path.join(__dirname, 'src/'),
      runtime: this.props.lambdaRuntimePythonVersion,
      layers: [this.baseLayer],
      index: '{{project_name}}_proc/lambdas/hello_proc.py',  // FIXME update appropriate path to Lambda entry point
      handler: 'handler',
      environment: this.lambdaEnv,
    });

    this.props.mainBus.grantPutEventsTo(procFn);
    this.setupEventRule(procFn);
  }

  private createProcSqsHandler() {
    const procSqsFn = new PythonFunction(this, this.id + 'ProcHandler', {
      entry: path.join(__dirname, 'src/'),
      runtime: this.props.lambdaRuntimePythonVersion,
      layers: [this.baseLayer],
      index: '{{project_name}}_proc/lambdas/hello_proc.py',  // FIXME update appropriate path to Lambda entry point
      handler: 'sqs_handler',
      environment: this.lambdaEnv,
    });

    // this.props.mainBus.grantPutEventsTo(procSqsFn); // FIXME remove this if no use
    // this.setupEventRule(procSqsFn); // FIXME remove this if no use
  }

  private setupEventRule(fn: aws_lambda.Function) {
    const eventRule = new Rule(this, this.id + 'EventRule', {
      ruleName: this.id + 'EventRule',
      description: 'Rule to send {event_type.value} events to the {handler.function_name} Lambda',
      eventBus: this.props.mainBus,
    });

    eventRule.addTarget(new aws_events_targets.LambdaFunction(fn));
    eventRule.addEventPattern({
      source: ['ORCHESTRATOR'], // FIXME complete source to destination event mapping
      detailType: ['SequenceRunStateChange'],
    });
  }
}
