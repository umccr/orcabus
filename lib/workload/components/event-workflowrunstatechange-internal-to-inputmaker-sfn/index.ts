import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import * as cdk from 'aws-cdk-lib';

export interface WorkflowRunStateChangeInternalInputMakerProps {
  /* Object name prefixes */
  stateMachinePrefix: string;
  lambdaPrefix: string;
  /* Table configs */
  tableObj: dynamodb.ITableV2;
  tablePartitionName: string;
  /* Event trigger configs */
  eventBusObj: events.IEventBus;
  triggerSource: string;
  triggerStatus: string;
  triggerWorkflowName: string;
  outputSource: string;
  /* Workflow metadata constants */
  workflowName: string;
  workflowVersion: string;
  payloadVersion: string;
  /* Nested state machine */
  inputStateMachineObj: sfn.IStateMachine;
}

export class WorkflowRunStateChangeInternalInputMakerConstruct extends Construct {
  public readonly stepFunctionObj: sfn.StateMachine;
  public readonly detailType = 'WorkflowRunStateChange';

  constructor(scope: Construct, id: string, props: WorkflowRunStateChangeInternalInputMakerProps) {
    super(scope, id);

    /*
        Part 1 - Generate the three lambdas required for the statemachine
        */

    /* Generate the portal run id lambda */
    const generatePortalRunIdLambdaObj = new PythonFunction(this, 'generate_portal_run_id_lambda', {
      functionName: `${props.lambdaPrefix}-generate-portal-run-id`,
      entry: path.join(__dirname, 'lambdas', 'generate_portal_run_id_py'),
      index: 'generate_portal_run_id.py',
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
    });

    /* Generate the workflow run name lambda */
    const generateWorkflowRunNameLambdaObj = new PythonFunction(
      this,
      'generate_workflow_run_name_lambda',
      {
        functionName: `${props.lambdaPrefix}-generate-workflow-run-name`,
        entry: path.join(__dirname, 'lambdas', 'generate_workflow_run_name_py'),
        index: 'generate_workflow_run_name.py',
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
      }
    );

    /* Generate the workflow run name lambda */
    const fillPlaceholdersInEventPayloadDataLambdaObj = new PythonFunction(
      this,
      'fill_placeholders_in_event_payload_data_lambda',
      {
        functionName: `${props.lambdaPrefix}-fill-placeholders-in-event-payload-data`,
        entry: path.join(__dirname, 'lambdas', 'fill_placeholders_in_event_payload_data_py'),
        index: 'fill_placeholders_in_event_payload_data.py',
        runtime: lambda.Runtime.PYTHON_3_11,
        architecture: lambda.Architecture.ARM_64,
      }
    );

    /*
    Part 2 - Build the AWS State Machine
    */
    this.stepFunctionObj = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: `${props.stateMachinePrefix}-input-maker-wrapper-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'workflowrunstatechange_input_maker_step_function_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_portal_run_id_lambda_function_arn__:
          generatePortalRunIdLambdaObj.currentVersion.functionArn,
        __update_portal_run_id_in_event_detail_lambda_function_arn__:
          fillPlaceholdersInEventPayloadDataLambdaObj.currentVersion.functionArn,
        __generate_workflow_run_name_lambda_function_arn__:
          generateWorkflowRunNameLambdaObj.currentVersion.functionArn,
        /* Table configurations */
        __table_name__: props.tableObj.tableName,
        /* Event configurations */
        __event_output_source__: props.outputSource,
        __detail_type__: this.detailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        __id_type__: props.tablePartitionName,
        /* Workflow name */
        __workflow_name__: props.workflowName,
        __workflow_version__: props.workflowVersion,
        __payload_version__: props.payloadVersion,
        /* Nested statemachine */
        __input_maker_state_machine_arn__: props.inputStateMachineObj.stateMachineArn,
      },
    });

    /*
        Part 3 - Connect permissions
        */
    /* Allow step functions to invoke the lambda */
    [
      generatePortalRunIdLambdaObj,
      generateWorkflowRunNameLambdaObj,
      fillPlaceholdersInEventPayloadDataLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(<iam.IRole>this.stepFunctionObj.role);
    });

    /* Allow step function to write to table */
    props.tableObj.grantReadWriteData(<iam.IRole>this.stepFunctionObj.role);

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    this.stepFunctionObj.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );
    props.inputStateMachineObj.grantStartExecution(<iam.IRole>this.stepFunctionObj.role);

    /* Allow step function to send events */
    props.eventBusObj.grantPutEventsTo(<iam.IRole>this.stepFunctionObj.role);

    /*
        Part 4 - Set up a rule to trigger the state machine
        */
    const rule = new events.Rule(this, 'workflowrunstatechangeparser_event_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [props.triggerSource],
        detailType: [this.detailType],
        detail: {
          status: [{ 'equals-ignore-case': props.triggerStatus }],
          workflowName: [{ 'equals-ignore-case': props.triggerWorkflowName }],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(this.stepFunctionObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
