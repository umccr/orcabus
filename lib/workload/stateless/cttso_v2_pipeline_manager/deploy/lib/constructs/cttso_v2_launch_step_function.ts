import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager'
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface ctTSOv2LaunchStepFunctionConstructProps {
  /* Stack Objects */
  dynamodb_table_obj: dynamodb.ITableV2,
  icav2_access_token_secret_obj: secretsManager.ISecret,
  lambda_layer_obj: LambdaLayerConstruct,
  icav2_copy_batch_state_machine_obj: sfn.IStateMachine,
  ssm_parameter_obj_list: ssm.IStringParameter[]; // List of parameters the workflow session state machine will need access to
  /* Lambdas paths */
  generate_trimmed_samplesheet_lambda_path: string; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  upload_samplesheet_to_cache_dir_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  generate_copy_manifest_dict_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  launch_cttso_nextflow_pipeline_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  /* Step function templates */
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_step_function.json'
}

export class ctTSOv2LaunchStepFunctionStateMachineConstruct extends Construct {

  public readonly cttso_v2_launch_state_machine_name: string;
  public readonly cttso_v2_launch_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: ctTSOv2LaunchStepFunctionConstructProps) {
    super(scope, id);

    // launch_cttso_nextflow_pipeline lambda
    const launch_cttso_nextflow_pipeline_lambda_obj = new PythonFunction(
      this,
      'launch_cttso_nextflow_pipeline_lambda_python_function',
      {
        entry: props.launch_cttso_nextflow_pipeline_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
        environment: {
          "ICAV2_ACCESS_TOKEN_SECRET_ID": props.icav2_access_token_secret_obj.secretName
        }
      }
    );

    // Add icav2 secrets permissions to lambda
    props.icav2_access_token_secret_obj.grantRead(
      // @ts-ignore
      <iam.IRole>launch_cttso_nextflow_pipeline_lambda_obj.role
    )

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach(
      (ssm_parameter_obj) => {
        ssm_parameter_obj.grantRead(
          // @ts-ignore
          <iam.IRole>launch_cttso_nextflow_pipeline_lambda_obj.role
        )
      },
    );

    // generate_copy_manifest_dict lambda
    // Doesnt need any ssm parameters
    const generate_copy_manifest_dict_lambda_obj = new PythonFunction(
      this,
      'generate_copy_manifest_dict_lambda_python_function',
      {
        entry: props.generate_copy_manifest_dict_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // Generate trimmed samplesheet lambda
    // Also doesn't need any ssm parameters or secrets
    const generate_trimmed_samplesheet_lambda_obj = new PythonFunction(
      this,
      'generate_trimmed_samplesheet_lambda_python_function',
      {
        entry: props.generate_trimmed_samplesheet_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // upload_samplesheet_to_cache_dir lambda
    const upload_samplesheet_to_cache_dir_lambda_obj = new PythonFunction(
      this,
      'upload_samplesheet_to_cache_dir_lambda_python_function',
      {
        entry: props.upload_samplesheet_to_cache_dir_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
        environment: {
          "ICAV2_ACCESS_TOKEN_SECRET_ID": props.icav2_access_token_secret_obj.secretName
        }
      }
    );

    // Add icav2 secrets permissions to lambda
    props.icav2_access_token_secret_obj.grantRead(
      // @ts-ignore
      <iam.IRole>upload_samplesheet_to_cache_dir_lambda_obj.role
    )

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach(
      (ssm_parameter_obj) => {
        ssm_parameter_obj.grantRead(
          // @ts-ignore
          <iam.IRole>upload_samplesheet_to_cache_dir_lambda_obj.role
        )
      },
    );

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'cttso_v2_launch_step_functions_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.workflow_definition_body_path),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__launch_cttso_nextflow_pipeline__': launch_cttso_nextflow_pipeline_lambda_obj.functionArn,
        '__generate_copy_manifest_dict__': generate_copy_manifest_dict_lambda_obj.functionArn,
        '__generate_trimmed_samplesheet__': generate_trimmed_samplesheet_lambda_obj.functionArn,
        '__upload_samplesheet_to_cache_dir__': upload_samplesheet_to_cache_dir_lambda_obj.functionArn,
        '__copy_batch_data_state_machine_arn__': props.icav2_copy_batch_state_machine_obj.stateMachineArn,
        '__table_name__': props.dynamodb_table_obj.tableName
      },
    });

    [
      launch_cttso_nextflow_pipeline_lambda_obj,
      generate_copy_manifest_dict_lambda_obj,
      generate_trimmed_samplesheet_lambda_obj,
      upload_samplesheet_to_cache_dir_lambda_obj,
    ].forEach(
      (lambda_obj) => {
        lambda_obj.grantInvoke(
          // @ts-ignore
          <iam.IRole>stateMachine.role
        )
      }
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

    // Add state machine execution permissions to stateMachine role
    props.icav2_copy_batch_state_machine_obj.grantStartSyncExecution(
      stateMachine.role
    )

    // Set outputs
    this.cttso_v2_launch_state_machine_name = stateMachine.stateMachineName;
    this.cttso_v2_launch_state_machine_arn = stateMachine.stateMachineArn;

  }

}
