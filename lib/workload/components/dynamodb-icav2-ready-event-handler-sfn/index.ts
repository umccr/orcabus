import { Construct } from 'constructs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { PythonLambdaUuidConstruct } from '../python-lambda-uuid-generator-function';

export interface WfmWorkflowStateChangeIcav2ReadyEventHandlerConstructProps {
  /* Names of table to write to */
  tableName: string; // Name of the table to get / update / query

  /* Names of the stateMachine to create */
  stateMachineName: string; // Name of the state machine to create

  /* The pipeline ID ssm parameter path */
  pipelineIdSsmPath: string; // Name of the pipeline id ssm parameter path we want to use as a backup

  /* Event configurations to push to  */
  detailType: string; // Detail type of the event to raise
  eventBusName: string; // Detail of the eventbus to push the event to
  triggerLaunchSource: string; // Source of the event that triggers the launch event
  internalEventSource: string; // What we push back to the orcabus

  /* State machines to run (underneath) */
  /* The inputs generation statemachine */
  generateInputsJsonSfn: sfn.IStateMachine;
  /* The internal sfn event we run */
  internalLaunchSfn: sfn.IStateMachine; // The arn of the internal step function that actually launches the icav2 analysis

  /* Internal workflowRunStateChange event details */
  workflowType: string;
  workflowVersion: string;
  serviceVersion: string;
}

export class WfmWorkflowStateChangeIcav2ReadyEventHandlerConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: WfmWorkflowStateChangeIcav2ReadyEventHandlerConstructProps
  ) {
    super(scope, id);

    // Get table object
    const table_obj = dynamodb.TableV2.fromTableName(this, 'table_obj', props.tableName);

    // Get the event bus object
    const eventbus_obj = events.EventBus.fromEventBusName(
      this,
      'orcabus_eventbus_obj',
      props.eventBusName
    );

    // Build the lambda python function to generate a uuid
    const uuid_lambda_obj = new PythonLambdaUuidConstruct(this, 'uuid_python').lambdaObj;

    // Collect the pipeline id from the ssm parameter store
    const pipeline_id_ssm_param_obj = ssm.StringParameter.fromStringParameterName(
      this,
      'pipeline_id_ssm_param_obj',
      props.pipelineIdSsmPath
    );

    // Build state machine object
    this.stateMachineObj = new sfn.StateMachine(this, 'state_machine', {
      stateMachineName: props.stateMachineName,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates/icav2_launch_workflow_and_raise_internal_event.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Table object */
        __table_name__: table_obj.tableName,
        /* Event metadata */
        __detail_type__: props.detailType,
        __eventbus_name__: props.eventBusName,
        __event_source__: props.internalEventSource,
        /* Put event details */
        __workflow_type__: props.workflowType,
        __workflow_version__: props.workflowVersion,
        __service_version__: props.serviceVersion,
        /* Lambdas */
        __generate_db_uuid_lambda_function_arn__: uuid_lambda_obj.functionArn,
        /* SSM Parameter paths */
        __pipeline_id_ssm_path__: pipeline_id_ssm_param_obj.parameterName,
        /* Step functions */
        __set_input_json_state_machine_arn__: props.generateInputsJsonSfn.stateMachineArn,
        __launch_state_machine_arn__: props.internalLaunchSfn.stateMachineArn,
      },
    });

    /* Grant the state machine access to invoke the dbuuid generator lambda function */
    uuid_lambda_obj.currentVersion.grantInvoke(this.stateMachineObj.role);

    /* Grant the state machine access to the ssm parameter path */
    pipeline_id_ssm_param_obj.grantRead(this.stateMachineObj.role);

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
    props.internalLaunchSfn.grantStartExecution(this.stateMachineObj.role);

    /* Grant the state machine read and write access to the table */
    table_obj.grantReadWriteData(this.stateMachineObj);

    // Create a rule for this state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: eventbus_obj,
      ruleName: `${props.stateMachineName}-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: ['ready'],
          workflow: [props.workflowType],
        },
      },
    });

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    /* Grant the state machine the ability to submit events to the event bus */
    eventbus_obj.grantPutEventsTo(this.stateMachineObj.role);
  }
}
