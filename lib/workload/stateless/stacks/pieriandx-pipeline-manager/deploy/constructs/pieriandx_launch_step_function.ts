import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';

interface PieriandxLaunchStepFunctionConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  /* workflow */
  workflowName: string;
  workflowVersion: string;
  /* lambda paths */
  generatePieriandxObjectsLambdaObj: PythonFunction; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  /* Defaults */
  defaultDagVersion: string;
  defaultPanelName: string;
  /* SSM Parameters */
  dagSsmParameterObj: ssm.IStringParameter;
  panelNameSsmParameterObj: ssm.IStringParameter;
  s3SequencerRunRootSsmParameterObj: ssm.IStringParameter;
  /* Step function templates */
  launchPieriandxStepfunctionTemplate: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'
  launchPieriandxCaseCreationStepfunctionObj: sfn.IStateMachine;
  launchPieriandxInformaticsjobCreationStepfunctionObj: sfn.IStateMachine;
  launchPieriandxSequencerrunCreationStepfunctionObj: sfn.IStateMachine;
  /* Events */
  payloadVersion: string;
  eventBusName: string;
  detailType: string;
  eventSource: string;
  triggerLaunchSource: string;
  /* Custom */
  prefix: string;
}

export class PieriandxLaunchStepFunctionStateMachineConstruct extends Construct {
  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: PieriandxLaunchStepFunctionConstructProps) {
    super(scope, id);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'pieriandx_launch_step_functions_state_machine',
      {
        // state machine name
        stateMachineName: `${props.prefix}-submit-sfn`,
        // definition template
        definitionBody: DefinitionBody.fromFile(props.launchPieriandxStepfunctionTemplate),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Table */
          __table_name__: props.dynamodbTableObj.tableName,
          __workflow_name__: props.workflowName,
          __workflow_version__: props.workflowVersion,

          /* Lambda Functions */
          __generate_pieriandx_objects_lambda_function_arn__:
            props.generatePieriandxObjectsLambdaObj.currentVersion.functionArn,

          /* Child step functions */
          __create_case_sfn__: props.launchPieriandxCaseCreationStepfunctionObj.stateMachineArn,
          __create_informaticsjob_sfn__:
            props.launchPieriandxInformaticsjobCreationStepfunctionObj.stateMachineArn,
          __create_sequencerrun_sfn__:
            props.launchPieriandxSequencerrunCreationStepfunctionObj.stateMachineArn,

          /* SSM Parameters */
          __dag_versions_ssm_parameter__: props.dagSsmParameterObj.parameterName,
          __panel_names_ssm_parameter__: props.panelNameSsmParameterObj.parameterName,

          /* Defaults / Hardcoded values */
          __default_dag_version__: props.defaultDagVersion,
          __default_panel_name__: props.defaultPanelName,
          __sequencerrun_s3_path_root__: props.s3SequencerRunRootSsmParameterObj.stringValue,

          /* Events */
          __payload_version__: props.payloadVersion,
          __event_bus_name__: props.eventBusName,
          __event_detail_type__: props.detailType,
          __event_source__: props.eventSource,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    props.generatePieriandxObjectsLambdaObj.currentVersion.grantInvoke(stateMachine);

    // Grant read permissions to the ssm parameters
    [
      props.dagSsmParameterObj,
      props.panelNameSsmParameterObj,
      props.s3SequencerRunRootSsmParameterObj,
    ].forEach((ssmParameterObj: ssm.IStringParameter) => {
      // Grant read permissions to the state machine
      ssmParameterObj.grantRead(stateMachine);
    });

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine.role);

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // Allow sub-state launch machines to be invoked by this statemachine
    [
      props.launchPieriandxCaseCreationStepfunctionObj,
      props.launchPieriandxInformaticsjobCreationStepfunctionObj,
      props.launchPieriandxSequencerrunCreationStepfunctionObj,
    ].forEach((state_machine_obj) => {
      state_machine_obj.grantStartExecution(stateMachine);
    });

    // Get event bus from event bus name
    const eventBusObj = events.EventBus.fromEventBusName(this, 'eventBus', props.eventBusName);

    // Add permissions to the state machine to send events to the event bus
    eventBusObj.grantPutEventsTo(stateMachine);

    // Create a rule for this state machine
    const rule = new events.Rule(this, 'rule', {
      eventBus: eventBusObj,
      ruleName: `${props.prefix}-launch-wrsc-rule`,
      eventPattern: {
        source: [props.triggerLaunchSource],
        detailType: [props.detailType],
        detail: {
          status: ['READY'],
          workflowName: [{ 'equals-ignore-case': props.workflowName }],
        },
      },
    });

    /* Add rule as a target to the state machine */
    rule.addTarget(
      new events_targets.SfnStateMachine(stateMachine, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );

    // Set outputs
    this.stateMachineObj = stateMachine;
  }
}
