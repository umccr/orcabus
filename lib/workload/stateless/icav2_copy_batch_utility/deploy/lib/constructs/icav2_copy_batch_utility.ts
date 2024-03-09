import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';


export interface ICAv2CopyBatchUtilityConstructProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer_path: string; // __dirname + '/../../../layers
  manifest_handler_lambda_path: string; // __dirname + '/../../../lambdas/manifest_handler'
  copy_batch_data_lambda_path: string; // __dirname + '/../../../lambdas/copy_batch_data_handler'
  job_status_handler_lambda_path: string; // __dirname + '/../../../lambdas/job_status_handler'
  definition_body_path: string; // __dirname + '/../../../step_functions_templates/copy_batch_state_machine.json'
}

export class ICAv2CopyBatchUtilityConstruct extends Construct {

  private icav2_jwt_ssm_parameter_path: string;
  private icav2_jwt_secret_arn_value: string;
  public readonly icav2_copy_batch_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: ICAv2CopyBatchUtilityConstructProps) {
    super(scope, id);

    // Import external ssm parameters
    this.set_jwt_secret_arn_object(props.icav2_jwt_ssm_parameter_path);

    // Generate lambda layer
    const lambda_layer = new LambdaLayerConstruct(
      this, 'lambda_layer', {
        layer_directory: props.lambdas_layer_path,
        layer_name: 'icav2_copy_batch_utility_tools'
      });

    // Manifest inverter lambda
    const manifest_inverter_lambda = new PythonFunction(this, 'manifest_inverter_lambda', {
      entry: props.manifest_handler_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj]
    });

    // Copy batch data handler lambda
    const copy_batch_data_lambda = new PythonFunction(this, 'copy_batch_data_lambda_python_function', {
      entry: props.copy_batch_data_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj],
      // @ts-ignore
      timeout: Duration.seconds(300),
    });

    // Job Status Handler
    const job_status_handler_lambda = new PythonFunction(this, 'job_status_handler_lambda', {
      entry: props.job_status_handler_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj],
      // @ts-ignore // We go through at least 10 jobs now to check if they're completed
      timeout: Duration.seconds(300),
    });

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'copy_batch_state_machine', {
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.definition_body_path),
      // Definition Substitutions
      definitionSubstitutions: {
        '__manifest_inverter_lambda_arn__': manifest_inverter_lambda.functionArn,
        '__copy_batch_data_lambda_arn__': copy_batch_data_lambda.functionArn,
        '__job_status_handler_lambda_arn__': job_status_handler_lambda.functionArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachine.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            manifest_inverter_lambda.functionArn,
            copy_batch_data_lambda.functionArn,
            job_status_handler_lambda.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );

    // Update lambda policies
    [
      copy_batch_data_lambda,
      job_status_handler_lambda
    ].forEach(
      lambda_function => {
        this.add_icav2_secrets_permissions_to_lambda(
          lambda_function,
        );
      }
    );

    // Set outputs
    this.icav2_copy_batch_state_machine_arn = stateMachine.stateMachineArn;
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

}

