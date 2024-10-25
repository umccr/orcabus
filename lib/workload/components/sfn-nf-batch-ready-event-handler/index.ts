/*
SFN NF Batch Ready event wrapper

This wrapper will run an AWS step function and connect your ready event, to AWS batch.
*/

import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
//import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as batch from 'aws-cdk-lib/aws-batch';

export interface WfmWorkflowStateChangeNfBatchReadyEventHandlerConstructProps {
  /* Names of table to write to */
  tableObj: dynamodb.ITableV2; // Name of the table to get / update / query

  /* Names of the stateMachine to create */
  stateMachinePrefix: string; // Name of the state machine to create

  /* The pipeline ID ssm parameter path */
  pipelineVersionSsmObj: ssm.IStringParameter; // Name of the pipeline version ssm parameter path we want to use

  /* Event configurations to push to */
  eventBusObj: events.IEventBus; // Detail of the eventbus to push the event to
  detailType: string; // Detail type of the event to raise
  triggerLaunchSource: string; // Source of the event that triggers the launch event
  internalEventSource: string; // What we push back to the orcabus

  /* State machines to run (underneath) */
  /* The Batch generation statemachine */
  generateBatchInputsLambdaObj: lambda_python.PythonFunction; // The lambda object to run to generate the batch

  /* Batch details */
  batchJobQueueObj: batch.IJobQueue; // The job queue to run the job on
  batchJobDefinitionObj: batch.IJobDefinition; // The job definition to run

  /* Internal workflowRunStateChange event details */
  workflowName?: string; // Required if addRule is true

  /*
  Custom addRule flag to allow for the addition of an event rule to the state machine
  Default is true
  */
  addRule?: boolean;
  targetRule?: events.Rule;
}

export class WfmWorkflowStateChangeNfBatchReadyEventHandlerConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;
  private readonly globals = {
    defaultAddRule: true,
    eventTriggerStatus: 'READY',
    eventSubmissionStatus: 'SUBMITTED',
    portalRunTablePartitionName: 'portal_run_id',
    eventDetailType: 'WorkflowRunStateChange',
    serviceVersion: '2024.10.17',
  };

  constructor(
    scope: Construct,
    id: string,
    props: WfmWorkflowStateChangeNfBatchReadyEventHandlerConstructProps
  ) {
    super(scope, id);

    // Build state machine object
    this.stateMachineObj = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: `${props.stateMachinePrefix}-wfm-nf-ready-batch-submit-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates/launch_nextflow_pipeline_template.asl.json')
      ),
      definitionSubstitutions: {
        /* Table object */
        __table_name__: props.tableObj.tableName,
        /* Table Partitions */
        __portal_run_table_partition_name: this.globals.portalRunTablePartitionName,
        /* Event metadata */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_detail_type__: this.globals.eventDetailType,
        __event_detail_version__: this.globals.serviceVersion,
        __event_source__: props.internalEventSource,
        __event_status__: this.globals.eventSubmissionStatus,
        /* Batch details */
        __job_queue_name__: props.batchJobQueueObj.jobQueueName,
        __job_definition_arn__: props.batchJobDefinitionObj.jobDefinitionArn,
        /* Lambdas */
        __generate_payload_lambda_function_arn__:
          props.generateBatchInputsLambdaObj.currentVersion.functionArn,
        /* SSM Parameter paths */
        __pipeline_version_ssm_path__: props.pipelineVersionSsmObj.parameterName,
      },
    });

    /* Grant the state machine access to invoke the launch lambda function */
    props.generateBatchInputsLambdaObj.currentVersion.grantInvoke(this.stateMachineObj);

    /* Grant the state machine access to the ssm parameter path */
    props.pipelineVersionSsmObj.grantRead(this.stateMachineObj);

    /* Grant the state machine read and write access to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Grant the state machine the ability to submit batch jobs to the job queue */
    // https://stackoverflow.com/a/76962105/6946787
    const submitJobPolicy = new iam.Policy(this, 'submitJobPolicy', {
      statements: [
        new iam.PolicyStatement({
          actions: ['batch:SubmitJob', 'batch:TagResource'],
          resources: [
            props.batchJobDefinitionObj.jobDefinitionArn,
            props.batchJobQueueObj.jobQueueArn,
          ],
        }),
      ],
    });

    //Attach the new policy to the state machine
    submitJobPolicy.attachToRole(this.stateMachineObj.role);

    /* Grant the state machine the ability to submit events to the event bus */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    // Create a rule for this state machine if the addRule flag is set to true or null
    if (props.addRule === true || (props.addRule === null && this.globals.defaultAddRule)) {
      this.addRule(props);
    }

    if (props.targetRule !== null && props.targetRule !== undefined) {
      /* Use the target rule provided */
      /* Add rule as a target to the state machine */
      props.targetRule.addTarget(
        new events_targets.SfnStateMachine(this.stateMachineObj, {
          input: events.RuleTargetInput.fromEventPath('$.detail'),
        })
      );
    }
  }

  addRule(props: WfmWorkflowStateChangeNfBatchReadyEventHandlerConstructProps) {
    /*
    Confirm that the property workflowName is not null
    */
    if (props.workflowName === null) {
      throw new Error('Workflow name must be provided when addRule is true');
    }

    const rule = new events.Rule(this, 'rule', {
      eventBus: props.eventBusObj,
      ruleName: `${props.stateMachinePrefix}-ready-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: [this.globals.eventTriggerStatus],
          workflowName: [{ 'equals-ignore-case': props.workflowName }],
        },
      },
    });

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
