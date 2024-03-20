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

interface BclConvertInterOpQcLaunchStepFunctionConstructProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer_path: string; // __dirname + '/../../../layers
  launch_bclconvert_interop_qc_cwl_pipeline_lambda_path: string; // __dirname + '/../../../lambdas/launch_bclconvert_interop_qc'
  interop_qc_pipeline_dynamodb_arn: string; // "arn:aws:dynamodb:ap-southeast-2:123456789012:table/interop_qc_pipeline"
  ssm_parameter_list: string[]; // List of parameters the workflow session state machine will need access to
  workflow_definition_body_path: string; // __dirname + '/../../../step_functions_templates/bclconvert_interop_qc_pipeline_manager.json'
}

export class BclConvertInteropQcLaunchStepFunctionStateMachineConstruct extends Construct {

  private icav2_jwt_secret_arn_value: string;
  private icav2_jwt_ssm_parameter_path: string;

  public readonly bclconvert_interop_qc_pipeline_launch_statemachine_arn: string;

  constructor(scope: Construct, id: string, props: BclConvertInterOpQcLaunchStepFunctionConstructProps) {
    super(scope, id);

    // Import external ssm parameters
    this.set_jwt_secret_arn_object(props.icav2_jwt_ssm_parameter_path);

    // Set lambda layer arn object
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: props.lambdas_layer_path,
      });

    // launch_cttso_nextflow_pipeline lambda
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
        layers: [lambda_layer.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(60),
      }
    );

    // Add icav2 secrets permissions to lambda
    this.add_icav2_secrets_permissions_to_lambda(
      launch_bclconvert_interop_qc_lambda,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_list.forEach(
      (ssm_parameter_path) => {
        this.add_get_ssm_parameter_permission_to_lambda_role_policy(
          launch_bclconvert_interop_qc_lambda,
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
        '__launch_bclconvert_interop_qc_pipeline__': launch_bclconvert_interop_qc_lambda.functionArn,
        '__interop_qc_pipeline_dynamodb__': props.interop_qc_pipeline_dynamodb_arn,
        '__table_name__': "bclconvertInteropQcICAv2AnalysesDynamoDBTable" // FIXME - currently hardcoded
      },
    });

    // Add lambda execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            launch_bclconvert_interop_qc_lambda.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );

    // Add Dynamo DB permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            props.interop_qc_pipeline_dynamodb_arn,
          ],
          actions: [
            'dynamodb:PutItem',
            'dynamodb:UpdateItem',
            'dynamodb:GetItem',
            'dynamodb:DeleteItem',
          ],
        },
      ),
    );

    // Set outputs
    this.bclconvert_interop_qc_pipeline_launch_statemachine_arn = stateMachine.stateMachineArn;
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
