/*

Two main parts:

1. Generate a step function app that can submit an WorkflowRunStateChange event to the nextflow stack
2. Track events from the nextflow stack and update the state of the workflow run

*/

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { WfmWorkflowStateChangeNfBatchReadyEventHandlerConstruct } from '../../../../components/sfn-nf-batch-ready-event-handler';
import * as batch from 'aws-cdk-lib/aws-batch';
import { WfmWorkflowStateChangeNfBatchStateChangeEventHandlerConstruct } from '../../../../components/sfn-nf-batch-state-change-event-handler';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';

export interface OncoanalyserNfPipelineManagerConfig {
  /* Nf Pipeline analysis essentials */
  pipelineVersionSsmPath: string; // List of parameters the workflow session state machine will need access to
  /* Table to store analysis metadata */
  dynamodbTableName: string;
  /* Internal and external buses */
  eventBusName: string;
  /*
  Event handling
  */
  workflowTypePrefix: string;
  workflowVersion: string;
  serviceVersion: string;
  triggerLaunchSource: string;
  internalEventSource: string;
  detailType: string;
  /*
  Batch handling
  */
  batchJobQueueArn: string;
  batchJobDefinitionArn: string;
  /*
  Names for statemachines
  */
  stateMachinePrefix: string;
}

export type OncoanalyserNfPipelineManagerStackProps = OncoanalyserNfPipelineManagerConfig &
  cdk.StackProps;

export class OncoanalyserNfPipelineManagerStack extends cdk.Stack {
  private readonly dynamodbTableObj: dynamodb.ITableV2;
  private readonly eventBusObj: events.IEventBus;
  private readonly pipelineVersionSsmObj: ssm.IStringParameter;
  private readonly prefix = 'oncoanalyser';
  private readonly triggerLaunchStatus = 'READY';

  constructor(scope: Construct, id: string, props: OncoanalyserNfPipelineManagerStackProps) {
    super(scope, id, props);

    // Get dynamodb table for construct
    this.dynamodbTableObj = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodbTableName
    );

    // Set ssm parameter objects
    this.pipelineVersionSsmObj = ssm.StringParameter.fromStringParameterName(
      this,
      props.pipelineVersionSsmPath,
      props.pipelineVersionSsmPath
    );

    // Get event bus object
    this.eventBusObj = events.EventBus.fromEventBusName(this, 'event_bus', props.eventBusName);

    // Get the batch job queue
    const batchJobQueue = batch.JobQueue.fromJobQueueArn(
      this,
      'batch_job_queue',
      props.batchJobQueueArn
    );
    const batchJobDefinition = batch.EcsJobDefinition.fromJobDefinitionArn(
      this,
      'batch_job_definition',
      props.batchJobDefinitionArn
    );

    /*
    Build lambdas
    */
    const setBatchParametersLambdaObj = new PythonFunction(this, 'get_batch_parameters', {
      entry: path.join(__dirname, '../lambdas/generate_batch_parameters_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_batch_parameters.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /* Our own rules for the batch ready event */
    const rule = new events.Rule(this, 'rule', {
      eventBus: this.eventBusObj,
      ruleName: `${props.stateMachinePrefix}-ready-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: [this.triggerLaunchStatus],
          workflowName: [{ prefix: { 'equals-ignore-case': props.workflowTypePrefix } }],
        },
      },
    });

    // Create the step function to launch the ready event
    const nfBatchReadyConstruct = new WfmWorkflowStateChangeNfBatchReadyEventHandlerConstruct(
      this,
      'oncoanalyser_batch_ready_event_handler',
      {
        /* Names of table to write to */
        tableObj: this.dynamodbTableObj, // Name of the table to get / update / query

        /* Names of the stateMachine to create */
        stateMachinePrefix: this.prefix, // Name of the state machine to create

        /* The pipeline ID ssm parameter path */
        pipelineVersionSsmObj: this.pipelineVersionSsmObj, // Name of the pipeline version ssm parameter path we want to use

        /* Event configurations to push to */
        eventBusObj: this.eventBusObj, // Detail of the eventbus to push the event to
        detailType: props.detailType, // Detail type of the event to raise
        triggerLaunchSource: props.triggerLaunchSource, // Source of the event that triggers the launch event
        internalEventSource: props.internalEventSource, // What we push back to the orcabus

        /* State machines to run (underneath) */
        /* The Batch generation statemachine */
        generateBatchInputsLambdaObj: setBatchParametersLambdaObj, // The lambda object to run to generate the batch

        /* Batch details */
        // The job queue to run the job on
        batchJobQueueObj: batchJobQueue,
        // The job definition to run
        batchJobDefinitionObj: batchJobDefinition,

        /* Make our own rule */
        addRule: false,
        targetRule: rule,
      }
    );

    /*
    Part 2: Configure the lambdas and outputs step function
    Quite a bit more complicated than regular ICAv2 workflow setup since we need to
    1. Generate the outputs json from a nextflow pipeline (which doesn't have a json outputs endpoint)
    2. Delete the cache fastqs we generated in the configure inputs json step function
    */

    // Build the lambdas
    // Set the output json lambda
    const setOutputJsonLambdaObj = new PythonFunction(this, 'get_outputs_py', {
      entry: path.join(__dirname, '../lambdas/get_outputs_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'get_outputs.py',
      handler: 'handler',
      memorySize: 1024,
    });

    const nfStateChangeSfn = new WfmWorkflowStateChangeNfBatchStateChangeEventHandlerConstruct(
      this,
      'oncoanalyser_batch_state_change_event_handler',
      {
        /* Names of table to write to */
        tableObj: this.dynamodbTableObj, // Name of the table to get / update / query

        /* Names of the stateMachine to create */
        stateMachinePrefix: this.prefix, // Name of the state machine to create

        /* Event configurations to push to */
        eventBusObj: this.eventBusObj, // Detail of the eventbus to push the event to
        detailType: props.detailType, // Detail type of the event to raise
        triggerLaunchSource: props.triggerLaunchSource, // Source of the event that triggers the launch event
        internalEventSource: props.internalEventSource, // What we push back to the orcabus

        /* Lambda to collect outputs from workflow */
        /* The Batch generation statemachine */
        generateBatchOutputsLambdaObj: setOutputJsonLambdaObj, // The lambda object to run to generate the batch

        /* Batch details */
        batchJobDefinitionObj: batchJobDefinition, // The job definition to match in the event rule
      }
    );
  }
}
