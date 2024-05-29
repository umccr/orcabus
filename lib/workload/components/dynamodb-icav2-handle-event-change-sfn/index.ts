import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';

export interface Icav2AnalysisEventHandlerConstructProps {
  /* Names of objects to get */
  tableName: string; // Name of the table to get / update / query

  /* Names of objects to create */
  stateMachineName: string; // Name of the state machine to create

  /* Event configurations to push to  */
  detailType: string; // Detail type of the event to raise
  eventBusName: string; // Detail of the eventbus to push the event to
  icaEventPipeName: string; // Name of the ica event pipe this step function needs to subscribe to
  internalEventSource: string; // Source of the event we push

  /* Step function to generate the output json */
  generateOutputsJsonSfn: sfn.IStateMachine; // Step function to generate the output json

  /* Internal workflowRunStateChange event details */
  workflowName: string;
  workflowVersion: string;
  serviceVersion: string;
}

export class Icav2AnalysisEventHandlerConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: Icav2AnalysisEventHandlerConstructProps) {
    super(scope, id);

    // Get table object
    const table_obj = dynamodb.TableV2.fromTableName(this, 'table_obj', props.tableName);

    // Get the event bus object
    const eventbus_obj = events.EventBus.fromEventBusName(
      this,
      'orcabus_eventbus_obj',
      props.eventBusName
    );

    // Build state machine object
    this.stateMachineObj = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: props.stateMachineName,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/icav2_get_workflow_status_and_raise_internal_event.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table object */
        __table_name__: table_obj.tableName,
        /* Event metadata */
        __detail_type__: props.detailType,
        __eventbus_name__: props.eventBusName,
        __eventsource__: props.internalEventSource,
        /* Step function to generate the output json */
        __sfn_get_outputs_json__: props.generateOutputsJsonSfn.stateMachineArn,
        /* Put event details */
        __workflow_type__: props.workflowName,
        __workflow_version__: props.workflowVersion,
        __service_version__: props.serviceVersion,
      },
    });

    /* Grant the state machine read and write access to the table */
    table_obj.grantReadWriteData(this.stateMachineObj);

    /* Grant state machine permissions to run the output json step function */
    props.generateOutputsJsonSfn.grantStartExecution(this.stateMachineObj);

    /* Grant the state machine access to invoke the internal launch sfn machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    this.stateMachineObj.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Create a rule for this state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: eventbus_obj,
      ruleName: `${props.stateMachineName}-rule`,
      eventPattern: {
        detail: {
          'ica-event': {
            // ICA_EXEC_028 is an analysis state change in ICAv2
            eventCode: ['ICA_EXEC_028'],
          },
        },
      },
    });

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail.ica-event'),
      })
    );

    /* Grant the state machine the ability to submit events to the event bus */
    eventbus_obj.grantPutEventsTo(this.stateMachineObj.role);
  }
}
