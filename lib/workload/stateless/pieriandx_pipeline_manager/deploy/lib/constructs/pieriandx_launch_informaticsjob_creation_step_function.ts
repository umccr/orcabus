import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LambdaLayerConstruct } from './lambda_layer';

interface PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstructProps {
  /* Stack Objects */
  dynamodb_table_obj: dynamodb.ITableV2,
  pieriandx_collect_access_token_lambda_obj: lambda.IFunction,
  lambda_layer_obj: LambdaLayerConstruct,
  ssm_parameter_obj_list: ssm.IStringParameter[]; // List of parameters the workflow session state machine will need access to
  /* Lambdas paths */
  generate_informatics_job_lambda_path: string; // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
  /* Step function templates */
  launch_pieriandx_informaticsjob_creation_stepfunction_template: string; // __dirname + '/../../../step_functions_templates/launch_pieriandx_informaticsjob_creation.asl.json'
  /* PierianDx env vars */
  pieriandx_user_email: string; // services@umccr.org
  pieriandx_institution: string; // melbournetest / melbourne
  pieriandx_base_url: string; // https://app.uat.pieriandx.com/cgw-api/ / https://app.pieriandx.com/cgw-api/
}

export class PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct extends Construct {

  public readonly pieriandx_launch_informaticsjob_creation_state_machine_obj: sfn.IStateMachine;
  public readonly pieriandx_launch_informaticsjob_creation_state_machine_name: string;
  public readonly pieriandx_launch_informaticsjob_creation_state_machine_arn: string;

  constructor(scope: Construct, id: string, props: PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstructProps) {
    super(scope, id);

    // generate_db_uuid_lambda_path lambda
    // Doesnt need any ssm parameters
    const generate_informatics_job_lambda_obj = new PythonFunction(
      this,
      'generate_informatics_job_lambda_python_function',
      {
        entry: props.generate_informatics_job_lambda_path,
        runtime: lambda.Runtime.PYTHON_3_11,
        index: 'handler.py',
        handler: 'handler',
        memorySize: 1024,
        // @ts-ignore
        layers: [props.lambda_layer_obj.lambda_layer_version_obj],
        // @ts-ignore
        timeout: Duration.seconds(30),
        environment: {
          'PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME': props.pieriandx_collect_access_token_lambda_obj.functionName,
          'PIERIANDX_USER_EMAIL': props.pieriandx_user_email,
          'PIERIANDX_INSTITUTION': props.pieriandx_institution,
          'PIERIANDX_BASE_URL': props.pieriandx_base_url
        },
      },
    );

    // Add icav2 secrets permissions to lambda
    props.pieriandx_collect_access_token_lambda_obj.grantInvoke(
      // @ts-ignore
      <iam.IRole>generate_informatics_job_lambda_obj.role,
    );

    // Add each of the ssm parameters to the lambda role policy
    props.ssm_parameter_obj_list.forEach(
      (ssm_parameter_obj) => {
        ssm_parameter_obj.grantRead(
          // @ts-ignore
          <iam.IRole>generate_informatics_job_lambda_obj.role,
        );
      },
    );


    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(this, 'pieriandx_launch_step_functions_state_machine', {
      // defintiontemplate
      definitionBody: DefinitionBody.fromFile(props.launch_pieriandx_informaticsjob_creation_stepfunction_template),
      // definitionSubstitutions
      definitionSubstitutions: {
        '__generate_informaticsjob_lambda__': generate_informatics_job_lambda_obj.functionArn,
        '__pieriandx_case_table_name__': props.dynamodb_table_obj.tableName,
      },
    });

    // Grant lambda invoke permissions to the state machine
    [
      generate_informatics_job_lambda_obj,
    ].forEach(
      (lambda_obj) => {
        lambda_obj.grantInvoke(
          // @ts-ignore
          <iam.IRole>stateMachine.role,
        );
      },
    );

    // Allow state machine to read/write to dynamodb table
    props.dynamodb_table_obj.grantReadWriteData(
      stateMachine.role,
    );

    // Set outputs
    this.pieriandx_launch_informaticsjob_creation_state_machine_name = stateMachine.stateMachineName;
    this.pieriandx_launch_informaticsjob_creation_state_machine_arn = stateMachine.stateMachineArn;
    this.pieriandx_launch_informaticsjob_creation_state_machine_obj = stateMachine;
  }

}
