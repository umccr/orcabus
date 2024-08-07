/*
Collect the engine parameters required for the workflow run state change to be set to ready
*/

import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { PythonLambdaUuidConstruct } from '../python-lambda-uuid-generator-function';
import { PythonLambdaFlattenListOfObjectsConstruct } from '../python-lambda-flatten-list-of-objects';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { Duration } from 'aws-cdk-lib';

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
  triggerDetailType?: string;
  outputSource: string;
  /* Workflow metadata constants */
  workflowName: string;
  workflowVersion: string;
  payloadVersion: string;
  /* SSM Parameter Objects */
  outputUriSsmParameterObj?: ssm.IStringParameter;
  logsUriSsmParameterObj?: ssm.IStringParameter;
  cacheUriSsmParameterObj?: ssm.IStringParameter;
  icav2ProjectIdSsmParameterObj?: ssm.IStringParameter;
  /* Secrets */
  icav2AccessTokenSecretObj: secretsManager.ISecret;
}

export class WorkflowDraftRunStateChangeToWorkflowRunStateChangeReadyConstruct extends Construct {
  public readonly stepFunctionObj: sfn.StateMachine;
  public readonly defaultTriggerDetailType = 'WorkflowDraftRunStateChange';
  public readonly outputDetailType = 'WorkflowRunStateChange';
  private readonly portalRunPartitionName = 'portal_run';

  constructor(scope: Construct, id: string, props: WorkflowRunStateChangeInternalInputMakerProps) {
    super(scope, id);

    /*
    Part 1 - Generate the ssm collector statemachine
    */
    /* Lambda to generate the input */
    /* Generate the workflow run name lambda */
    const fillPlaceholdersInEventPayloadDataLambdaObj = new PythonFunction(
      this,
      'fill_placeholders_in_event_payload_data_lambda',
      {
        functionName: `${props.lambdaPrefix}-fill-placeholders-in-event-payload-data`,
        entry: path.join(__dirname, 'lambdas', 'fill_placeholders_in_event_payload_data_py'),
        index: 'fill_placeholders_in_event_payload_data.py',
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        environment: {
          ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretName,
        },
        timeout: Duration.seconds(60),
      }
    );

    // Add permissions for the lambda to read from secrets manager
    props.icav2AccessTokenSecretObj.grantRead(
      fillPlaceholdersInEventPayloadDataLambdaObj.currentVersion
    );

    /* Flatten Object list py */
    const flattenObjectListLambdaObj = new PythonLambdaFlattenListOfObjectsConstruct(
      this,
      'flatten_object_list_lambda'
    ).lambdaObj;

    /* Generate the statemachine */
    const engineParameterGeneratorStateMachineSfn = new sfn.StateMachine(
      this,
      'ssm_parameter_collector_state_machine',
      {
        stateMachineName: `${props.stateMachinePrefix}-engineparameter-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'generate_analysis_engine_parameters_from_ssm_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          __fill_placeholders_in_engine_parameters_lambda_function_arn__:
            fillPlaceholdersInEventPayloadDataLambdaObj.currentVersion.functionArn,
          __flatten_list_of_objects_lambda_function_arn__:
            flattenObjectListLambdaObj.currentVersion.functionArn,
        },
      }
    );

    // Add the permissions for the engineParameter state machine to read from SSM
    [
      props.outputUriSsmParameterObj,
      props.logsUriSsmParameterObj,
      props.cacheUriSsmParameterObj,
      props.icav2ProjectIdSsmParameterObj,
    ].forEach((ssmParameterObj) => {
      /* First check if the ssm parameter is defined */
      if (!ssmParameterObj) {
        // Skip
        return;
      }
      ssmParameterObj.grantRead(engineParameterGeneratorStateMachineSfn.role);
    });

    // Add permissions for the statemachine to fill in the placeholders
    [flattenObjectListLambdaObj, fillPlaceholdersInEventPayloadDataLambdaObj].forEach(
      (lambdaObj) => {
        lambdaObj.currentVersion.grantInvoke(engineParameterGeneratorStateMachineSfn.role);
      }
    );

    /*
    Part 2 - Build the AWS State Machine
    */
    /* Build the uuid generator lambda */
    const uuidGeneratorLambda = new PythonLambdaUuidConstruct(this, 'uuid_generator_lambda');

    // FIXME - sfn should check that the data object in the input
    // FIXME matches the dataobject in the database first before raising the event
    this.stepFunctionObj = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: `${props.stateMachinePrefix}-draft-to-ready-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'workflowrunstatechange_draft_to_ready_step_function_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_uuid_lambda_function_arn__:
          uuidGeneratorLambda.lambdaObj.currentVersion.functionArn,
        /* Table configurations */
        __table_name__: props.tableObj.tableName,
        __workflow_type_partition_name__: props.tablePartitionName,
        __portal_run_partition_name__: this.portalRunPartitionName,
        /* Event configurations */
        __event_output_source__: props.outputSource,
        __detail_type__: this.outputDetailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        /* Workflow name */
        __payload_version__: props.payloadVersion,
        /* Nested statemachine */
        __engine_parameters_maker_state_machine_arn__:
          engineParameterGeneratorStateMachineSfn.stateMachineArn,
        /* SSM Parameters */
        __output_uri_ssm_parameter_name__: props.outputUriSsmParameterObj?.parameterName || '',
        __logs_uri_ssm_parameter_name__: props.logsUriSsmParameterObj?.parameterName || '',
        __cache_uri_ssm_parameter_name__: props.cacheUriSsmParameterObj?.parameterName || '',
        __project_id_ssm_parameter_name__: props.icav2ProjectIdSsmParameterObj?.parameterName || '',
      },
    });

    /*
    Part 3 - Connect permissions
    */
    /* Allow step functions to invoke the lambda */
    [uuidGeneratorLambda.lambdaObj].forEach((lambdaObj) => {
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
    engineParameterGeneratorStateMachineSfn.grantStartExecution(
      <iam.IRole>this.stepFunctionObj.role
    );

    /* Allow step function to send events */
    props.eventBusObj.grantPutEventsTo(<iam.IRole>this.stepFunctionObj.role);

    /*
    Part 4 - Set up a rule to trigger the state machine
    */
    const rule = new events.Rule(this, 'workflowrunstatechangeparser_event_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [props.triggerSource],
        detailType: [props.triggerDetailType || this.defaultTriggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': props.triggerStatus }],
          workflowName: [{ 'equals-ignore-case': props.workflowName }],
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
