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


export interface ICAv2CopyBatchUtilityConstructProps {
  icav2_jwt_ssm_parameter_path: string;  // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  lambdas_layer_path: string; // __dirname + '/../../../layers
  manifest_handler_lambda_path: string; // __dirname + '/../../../lambdas/manifest_handler'
  check_or_launch_job_lambda_path: string; // __dirname + '/../../../lambdas/check_or_launch_job'
  state_machine_batch_definition_body_path: string; // __dirname + '/../../../step_functions_templates/copy_batch_state_machine.json'
  state_machine_single_definition_body_path: string; // __dirname + '/../../../step_functions_templates/copy_single_state_machine.json'
}

export class ICAv2CopyBatchUtilityConstruct extends Construct {

  private icav2_jwt_ssm_parameter_path: string;
  private icav2_jwt_secret_arn_value: string;
  public readonly icav2_copy_batch_state_machine_arn: string;
  public readonly icav2_copy_single_state_machine_arn: string;

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

    // Job Status Handler
    const check_or_launch_job_lambda = new PythonFunction(this, 'check_or_launch_job_lambda', {
      entry: props.check_or_launch_job_lambda_path,
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'handler.py',
      handler: 'handler',
      memorySize: 1024,
      // @ts-ignore
      layers: [lambda_layer.lambda_layer_version_obj],
      // @ts-ignore // We go through at least 10 jobs now to check if they're completed
      timeout: Duration.seconds(300),
    });

    // Specify the single statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineSingle = new sfn.StateMachine(this, 'copy_single_state_machine', {
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.state_machine_single_definition_body_path),
      // Definition Substitutions
      definitionSubstitutions: {
        '__check_or_launch_job_lambda_arn__': check_or_launch_job_lambda.functionArn,
      },
    });

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachineBatch = new sfn.StateMachine(this, 'copy_batch_state_machine', {
      // Definition Template
      definitionBody: DefinitionBody.fromFile(props.state_machine_batch_definition_body_path),
      // Definition Substitutions
      definitionSubstitutions: {
        '__manifest_inverter_lambda_arn__': manifest_inverter_lambda.functionArn,
        '__copy_single_job_state_machine_arn__': stateMachineSingle.stateMachineArn,
      },
    });

    // Add execution permissions to stateMachine role
    stateMachineBatch.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            manifest_inverter_lambda.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );

    // Add execution permissions to stateMachine role
    stateMachineSingle.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            check_or_launch_job_lambda.functionArn,
          ],
          actions: [
            'lambda:InvokeFunction',
          ],
        },
      ),
    );

      // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    stateMachineBatch.addToRolePolicy(
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

    // Add state machine execution permissions to stateMachineBatch role
    stateMachineBatch.addToRolePolicy(
      new iam.PolicyStatement(
        {
          resources: [
            stateMachineSingle.stateMachineArn,
          ],
          actions: [
            'states:StartExecution',
          ],
        },
      ),
    );

    // Update lambda policies
    [
      check_or_launch_job_lambda
    ].forEach(
      lambda_function => {
        this.add_icav2_secrets_permissions_to_lambda(
          lambda_function,
        );
      }
    );

    // Set outputs
    this.icav2_copy_batch_state_machine_arn = stateMachineBatch.stateMachineArn;
    this.icav2_copy_single_state_machine_arn = stateMachineSingle.stateMachineArn;
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

