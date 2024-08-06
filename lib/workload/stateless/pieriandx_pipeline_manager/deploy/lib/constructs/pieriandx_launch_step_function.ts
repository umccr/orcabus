import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface PieriandxLaunchStepFunctionConstructProps {
  /* Stack Objects */
  dynamodb_table_obj: dynamodb.ITableV2,
  lambda_layer_obj: LambdaLayerConstruct,
  ssm_parameter_obj_list: ssm.IStringParameter[]; // List of parameters the workflow session state machine will need access to
  /* lambda paths */
  generate_uuid_lambda_path: string; // __dirname + '/../../../lambdas/generate_db_uuid'
  generate_pieriandx_dx_objects_lambda_path: string; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  /* Step function templates */
  launch_pieriandx_stepfunction_template: string;  // __dirname + '/../../../step_functions_templates/cttso_v2_launch_workflow_state_machine.json'
  launch_pieriandx_case_creation_stepfunction_obj: sfn.IStateMachine;
  launch_pieriandx_informaticsjob_creation_stepfunction_obj: sfn.IStateMachine;
  launch_pieriandx_sequencerrun_creation_stepfunction_obj: sfn.IStateMachine;
}

export class PieriandxLaunchStepFunctionStateMachineConstruct extends Construct {

  public readonly pieriandx_launch_state_machine_name: string;
  public readonly pieriandx_launch_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: PieriandxLaunchStepFunctionConstructProps) {
    super(scope, id);

        // generate_db_uuid_lambda_path lambda
    // Doesnt need any ssm parameters
    const generate_db_uuid_lambda_obj = new PythonFunction(
      this,
      'generate_db_uuid_lambda_python_function',
      {
        entry: props.generate_uuid_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj]
      }
    );

    // launch_cttso_nextflow_pipeline lambda
    const generate_pieriandx_dx_objects_lambda_obj = new PythonFunction(
      this,
      'generate_pieriandx_dx_objects_lambda_python_function',
      {
        entry: props.generate_pieriandx_dx_objects_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(20)
      }
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach(
      (ssm_parameter_obj) => {
        ssm_parameter_obj.grantRead(
          // @ts-ignore
          <iam.IRole>generate_pieriandx_dx_objects_lambda_obj.role
        )
      },
    );


    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'pieriandx_launch_step_functions_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.launch_pieriandx_stepfunction_template),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__generate_uuid_lambda__': generate_db_uuid_lambda_obj.functionArn,
        '__generate_pieriandx_dx_objects_lambda__': generate_pieriandx_dx_objects_lambda_obj.functionArn,
        '__create_case_sfn__': props.launch_pieriandx_case_creation_stepfunction_obj.stateMachineArn,
        '__create_informaticsjob_sfn__': props.launch_pieriandx_informaticsjob_creation_stepfunction_obj.stateMachineArn,
        '__create_sequencerrun_sfn__': props.launch_pieriandx_sequencerrun_creation_stepfunction_obj.stateMachineArn,
        '__pieriandx_case_table_name__': props.dynamodb_table_obj.tableName
      },
    });

    // Grant lambda invoke permissions to the state machine
    [
      generate_db_uuid_lambda_obj,
      generate_pieriandx_dx_objects_lambda_obj
    ].forEach(
      (lambda_obj) => {
        lambda_obj.grantInvoke(
          // @ts-ignore
          <iam.IRole>stateMachine.role
        )
      }
    )

    // Allow state machine to read/write to dynamodb table
    props.dynamodb_table_obj.grantReadWriteData(
      stateMachine.role
    )

    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
          ],
          actions: [
            'events:PutTargets',
            'events:PutRule',
            'events:DescribeRule',
          ],
        },
      ),
    );

    // Allow sub-state launch machines to be invoked by this statemachine
    [
      props.launch_pieriandx_case_creation_stepfunction_obj,
      props.launch_pieriandx_informaticsjob_creation_stepfunction_obj,
      props.launch_pieriandx_sequencerrun_creation_stepfunction_obj,
    ].forEach(
      (state_machine_obj) => {
        state_machine_obj.grantStartExecution(
          <iam.IRole>stateMachine.role
        )
      }
    )

    // Set outputs
    this.pieriandx_launch_state_machine_name = stateMachine.stateMachineName;
    this.pieriandx_launch_state_machine_arn = stateMachine.stateMachineArn;

  }

}
