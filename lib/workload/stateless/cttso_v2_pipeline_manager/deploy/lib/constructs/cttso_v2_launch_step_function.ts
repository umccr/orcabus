import * as cdk from 'aws-cdk-lib';
import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface ctTSOv2LaunchStepFunctionConstructProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer_path: string; // __dirname + '/../../../layers
  get_cttso_cache_and_output_paths_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  generate_trimmed_samplesheet_lambda_path: string; // __dirname + '/../../../lambdas/generate_trimmed_samplesheet_lambda_path'
  upload_samplesheet_to_cache_dir_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  generate_copy_manifest_dict_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  launch_cttso_nextflow_pipeline_lambda_path: string; // __dirname + '/../../../lambdas/get_cttso_cache_and_output_paths'
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  icav2_copy_batch_state_machine_arn: string;
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/cttso_v2_launch_step_function.json'
}

export class ctTSOv2LaunchStepFunctionStateMachineConstruct extends Construct {

  private icav2_jwt_secret_arn_value: string;
  private icav2_jwt_ssm_parameter_path: string;

  public readonly cttso_v2_launch_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: ctTSOv2LaunchStepFunctionConstructProps) {
    super(scope, id);

    // Import external ssm parameters
    this.set_jwt_secret_arn_object(props.icav2_jwt_ssm_parameter_path);

    // Set lambda layer arn object
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: props.lambdas_layer_path,
      });

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
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // Add icav2 secrets permissions to lambda
    this.add_icav2_secrets_permissions_to_lambda(
      launch_cttso_nextflow_pipeline_lambda_obj,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_list.forEach(
      (ssm_parameter_path) => {
        this.add_get_ssm_parameter_permission_to_lambda_role_policy(
          launch_cttso_nextflow_pipeline_lambda_obj,
          ssm_parameter_path,
        );
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
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // get_cttso_cache_and_output_paths lambda
    const get_cttso_cache_and_output_paths_lambda_obj = new PythonFunction(
      this,
      'get_cttso_cache_and_output_paths_lambda_python_function',
      {
        entry: props.get_cttso_cache_and_output_paths_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // Add icav2 secrets permissions to lambda
    this.add_icav2_secrets_permissions_to_lambda(
      get_cttso_cache_and_output_paths_lambda_obj,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_list.forEach(
      (ssm_parameter_path) => {
        this.add_get_ssm_parameter_permission_to_lambda_role_policy(
          get_cttso_cache_and_output_paths_lambda_obj,
          ssm_parameter_path,
        );
      },
    );

    // Generate trimmed samplesheet lambda
    // Also doesn't need any ssm parameters or secrets
    // generate_trimmed_samplesheet
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
        layers: [lambda_layer.lambda_layer_version_obj],
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
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // Add icav2 secrets permissions to lambda
    this.add_icav2_secrets_permissions_to_lambda(
      upload_samplesheet_to_cache_dir_lambda_obj,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_list.forEach(
      (ssm_parameter_path) => {
        this.add_get_ssm_parameter_permission_to_lambda_role_policy(
          upload_samplesheet_to_cache_dir_lambda_obj,
          ssm_parameter_path,
        );
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
        '__get_cttso_cache_and_output_paths__': get_cttso_cache_and_output_paths_lambda_obj.functionArn,
        '__generate_trimmed_samplesheet__': generate_trimmed_samplesheet_lambda_obj.functionArn,
        '__upload_samplesheet_to_cache_dir__': upload_samplesheet_to_cache_dir_lambda_obj.functionArn,
        '__copy_batch_data_state_machine_arn__': props.icav2_copy_batch_state_machine_arn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            launch_cttso_nextflow_pipeline_lambda_obj.functionArn,
            generate_copy_manifest_dict_lambda_obj.functionArn,
            get_cttso_cache_and_output_paths_lambda_obj.functionArn,
            generate_trimmed_samplesheet_lambda_obj.functionArn,
            upload_samplesheet_to_cache_dir_lambda_obj.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );


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
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            props.icav2_copy_batch_state_machine_arn,
          ],
          actions: [
            'states:StartExecution',
          ],
        },
      ),
    );

    // // Allow statemachine execution check access to describe the copy batch state machine execution
    // execution_check_status_lambda_path.addToRolePolicy(
    //   // @ts-ignore
    //   new iam.PolicyStatement(
    //     {
    //       resources: [
    //         props.icav2_copy_batch_state_machine_arn,
    //       ],
    //       actions: [
    //         'states:DescribeExecution',
    //       ],
    //     },
    //   ),
    // );

    // Set outputs
    this.cttso_v2_launch_state_machine_arn = stateMachine.stateMachineArn;

  }

  private set_jwt_secret_arn_object(icav2_jwt_ssm_parameter_path: string) {
    const icav2_jwt_ssm_parameter = ssm.StringParameter.fromStringParameterName(
      this,
      'get_jwt_secret_arn_value',
      icav2_jwt_ssm_parameter_path,
    );

    this.icav2_jwt_ssm_parameter_path = icav2_jwt_ssm_parameter.parameterArn;
    this.icav2_jwt_secret_arn_value = icav2_jwt_ssm_parameter.stringValue;
  }

  private add_icav2_secrets_permissions_to_lambda(
    lambda_function: lambda.Function | PythonFunction,
  ) {
    /*
    Add the statement that allows
    */
    lambda_function.addToRolePolicy(
      // @ts-ignore
      new iam.PolicyStatement(
        {
          resources: [
            this.icav2_jwt_secret_arn_value,
            this.icav2_jwt_ssm_parameter_path,
          ],
          actions: [
            'secretsmanager:GetSecretValue',
            'ssm:GetParameter',
          ],
        },
      ),
    );
  }

  private add_get_ssm_parameter_permission_to_lambda_role_policy(
    lambda_function: lambda.Function | PythonFunction, ssm_parameter_path: string,
  ) {
    lambda_function.addToRolePolicy(
      // @ts-ignore
      new iam.PolicyStatement(
        {
          resources: [
            `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter${ssm_parameter_path}`,
          ],
          actions: [
            'ssm:GetParameter',
          ],
        },
      ),
    );
  }

}
