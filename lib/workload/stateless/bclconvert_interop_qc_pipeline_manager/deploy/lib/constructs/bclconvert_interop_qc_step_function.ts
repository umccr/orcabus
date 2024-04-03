import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface BclConvertInterOpQcLaunchStepFunctionConstructProps {
  // Stack objects
  dynamodb_table_obj: dynamodb.ITableV2; // dynamodb table object
  icav2_access_token_secret_obj: secretsManager.ISecret;  // "ICAv2Jwticav2-credentials-umccr-service-user-trial"
  lambda_layer_obj: LambdaLayerConstruct; // Lambda layer object
  // Lambda Layer Paths
  generate_uuid_lambda_path: string; // __dirname + '/../../../lambdas/generate_db_uuid'
  launch_bclconvert_interop_qc_cwl_pipeline_lambda_path: string; // __dirname + '/../../../lambdas/launch_bclconvert_interop_qc'
  // Step function template paths
  launch_workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/bclconvert_interop_qc_pipeline_manager.json'
  state_change_definition_body_path: string; // __dirname + '/../../../step_functions_templates/handle_state_change_template.json'
  // Step function object list
  ssm_parameter_obj_list: ssm.IStringParameter[]; // List of parameters the workflow session state machine will need access to
}

export class BclConvertInteropQcLaunchStepFunctionStateMachineConstruct extends Construct {

  public readonly bclconvert_interop_qc_pipeline_launch_statemachine_arn: string;
  public readonly bclconvert_interop_qc_pipeline_external_state_change_statemachine_arn: string;

  constructor(scope: Construct, id: string, props: BclConvertInterOpQcLaunchStepFunctionConstructProps) {
    super(scope, id);

    /*
    Aim of this construct is to generate a cloudformation construct with the following attributes

    1. A step function state machine that will launch the bclconvert_interop_qc pipeline
    2. A step function state machine that will handle external state changes of analyses

    These state machines will be generated from the definition templates provided in the props

    The launch bclconvert interop qc statemachine will need a lambda function to launch the cwl pipeline
    The generate db uuid lambda will be used to generate a unique id for the dynamodb table

    We update the dynamodb table at the end of the launch pipeline analysis step function.

    We also generate an internal event at the end of each pipeline to inform any subscribing services that the state of the analysis has changed
    */

    // launch_bclconvert_interop_qc_pipeline lambda
    const launch_bclconvert_interop_qc_lambda = new PythonFunction(
      this,
      'launch_bclconvert_interop_qc_launch_lambda_python_function',
      {
        entry: props.launch_bclconvert_interop_qc_cwl_pipeline_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
        environment: {
          'ICAV2_ACCESS_TOKEN_SECRET_ID': props.icav2_access_token_secret_obj.secretName
        }
      }
    );

    // Generate DB UUID Lambda
    const generate_db_uuid_lambda = new PythonFunction(
      this,
      'generate_db_uuid_lambda_python_function',
      {
        entry: props.generate_uuid_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
      }
    );

    // Add secrets to lambda role policy
    props.icav2_access_token_secret_obj.grantRead(
      // @ts-ignore
      launch_bclconvert_interop_qc_lambda.role
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach(
      (ssm_parameter_obj) => {
        ssm_parameter_obj.grantRead(
          // @ts-ignore
          <iam.IRole>launch_bclconvert_interop_qc_lambda.role
        )
      },
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const launchStateMachine = new sfn.StateMachine(this, 'bclconvert_interop_launch_step_functions_state_machine', {
      // defintion template
      definitionBody: DefinitionBody.fromFile(props.launch_workflow_definition_body_path),
      // definition substitutions
      definitionSubstitutions: {
        '__launch_bclconvert_interop_qc_pipeline__': launch_bclconvert_interop_qc_lambda.functionArn,
        '__generate_db_uuid__': generate_db_uuid_lambda.functionArn,
        '__table_name__': props.dynamodb_table_obj.tableName
      },
    });

    // Generate state machine for handling state change
    const handleExternalStateChangeStateMachine = new sfn.StateMachine(this, 'external_statechange_sfn', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.state_change_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__table_name__': props.dynamodb_table_obj.tableName
      },
    });

    // Add lambda execution permissions to launch stateMachine
    [
      generate_db_uuid_lambda,
      launch_bclconvert_interop_qc_lambda
    ].forEach(
      (lambda_function) => {
        lambda_function.grantInvoke(
          // @ts-ignore
          <iam.IRole>launchStateMachine.role
        )
      },
    );

    // Add dynamodb permissions to stateMachines
    [
      launchStateMachine,
      handleExternalStateChangeStateMachine
    ].forEach(
      (state_machine) => {
         props.dynamodb_table_obj.grantReadWriteData(
          <iam.IRole>state_machine.role,
        );
      },
    );

    // Set outputs
    this.bclconvert_interop_qc_pipeline_launch_statemachine_arn = launchStateMachine.stateMachineArn;
    this.bclconvert_interop_qc_pipeline_external_state_change_statemachine_arn = handleExternalStateChangeStateMachine.stateMachineArn;
  }
}
