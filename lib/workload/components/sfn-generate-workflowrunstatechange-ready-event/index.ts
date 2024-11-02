/*
Collect the engine parameters required for the workflow run state change to be set to ready
*/

import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { PythonLambdaFlattenListOfObjectsConstruct } from '../python-lambda-flatten-list-of-objects';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { Duration } from 'aws-cdk-lib';

export interface WorkflowRunStateChangeInternalInputMakerProps {
  /* Object name prefixes */
  stateMachinePrefix: string;
  lambdaPrefix: string;
  /* Event trigger configs */
  eventBusObj: events.IEventBus;
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
  icav2AccessTokenSecretObj?: secretsManager.ISecret;
}

export class GenerateWorkflowRunStateChangeReadyConstruct extends Construct {
  public readonly stepFunctionObj: sfn.StateMachine;
  public readonly outputDetailType = 'WorkflowRunStateChange';
  private readonly readyStatus = 'READY';

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
        functionName: `${props.lambdaPrefix}-fill-engine-parameters`,
        entry: path.join(__dirname, 'lambdas', 'fill_placeholders_in_event_payload_data_py'),
        index: 'fill_placeholders_in_event_payload_data.py',
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        timeout: Duration.seconds(60),
      }
    );

    /*
   For ICAv2 workflows only
   */
    if (props.icav2AccessTokenSecretObj !== undefined) {
      /*
      Add the secret to the lambda environment
      */
      fillPlaceholdersInEventPayloadDataLambdaObj.addEnvironment(
        'ICAV2_ACCESS_TOKEN_SECRET_ID',
        props.icav2AccessTokenSecretObj.secretName
      );
      // Add permissions for the lambda to read from secrets manager
      props.icav2AccessTokenSecretObj.grantRead(
        fillPlaceholdersInEventPayloadDataLambdaObj.currentVersion
      );
    }

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
      ssmParameterObj.grantRead(engineParameterGeneratorStateMachineSfn);
    });

    // Add permissions for the statemachine to fill in the placeholders
    [flattenObjectListLambdaObj, fillPlaceholdersInEventPayloadDataLambdaObj].forEach(
      (lambdaObj) => {
        lambdaObj.currentVersion.grantInvoke(engineParameterGeneratorStateMachineSfn);
      }
    );

    /*
    Part 2 - Build the AWS State Machine
    */
    this.stepFunctionObj = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: `${props.stateMachinePrefix}-ready-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'workflowrunstatechange_generate_ready_step_function_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Event configurations */
        __event_output_source__: props.outputSource,
        __detail_type__: this.outputDetailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        __ready_status__: this.readyStatus,
        /* Workflow name */
        __workflow_name__: props.workflowName,
        __workflow_version__: props.workflowVersion,
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
    Part 3 - Connect permissions between state-machines
    */

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
    engineParameterGeneratorStateMachineSfn.grantStartExecution(this.stepFunctionObj);

    /* Allow step function to send events */
    props.eventBusObj.grantPutEventsTo(this.stepFunctionObj);
  }
}
