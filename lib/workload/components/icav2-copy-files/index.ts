import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';

export interface ICAv2CopyFilesConstructProps {
  /* Constructs */
  icav2JwtSecretParameterObj: secretsManager.ISecret; // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
  /* StateMachine paths */
  stateMachineName: string; // '{prefix}-copy-files-sfn'  i.e cttso-v2-copy-files-sfn or bssh-copy-files-sfn
}

export class ICAv2CopyFilesConstruct extends Construct {
  public readonly icav2CopyFilesSfnObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: ICAv2CopyFilesConstructProps) {
    super(scope, id);

    // Job Status Handler
    const check_or_launch_job_lambda = new PythonFunction(this, 'check_or_launch_job_lambda', {
      entry: path.join(__dirname, 'check_or_launch_job_lambda_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'check_or_launch_job_lambda.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(300),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2JwtSecretParameterObj.secretName,
      },
    });

    // Allow launch job lambda to read the secret
    props.icav2JwtSecretParameterObj.grantRead(
      <iam.Role>check_or_launch_job_lambda.currentVersion.role
    );

    // Specify the single statemachine and replace the arn placeholders with the lambda arns defined above
    this.icav2CopyFilesSfnObj = new sfn.StateMachine(this, 'copy_single_state_machine', {
      // Name
      stateMachineName: props.stateMachineName,
      // Definition Template
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates/copy_files_sfn.asl.json')
      ),
      // Definition Substitutions
      definitionSubstitutions: {
        __check_or_launch_job_lambda_arn__: check_or_launch_job_lambda.currentVersion.functionArn,
      },
    });

    // Add execution permissions to stateMachine role
    check_or_launch_job_lambda.currentVersion.grantInvoke(this.icav2CopyFilesSfnObj.role);
  }
}
