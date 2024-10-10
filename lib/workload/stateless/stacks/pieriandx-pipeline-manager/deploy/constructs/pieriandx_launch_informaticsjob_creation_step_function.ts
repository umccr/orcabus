import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

interface PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  /* Lambdas paths */
  generateInformaticsjobLambdaObj: PythonFunction; // __dirname + '/../../../lambdas/upload_samplesheet_to_cache_dir'
  /* Step function templates */
  launchPieriandxInformaticsjobCreationStepfunctionTemplate: string; // __dirname + '/../../../step_functions_templates/launch_pieriandx_informaticsjob_creation.asl.json'
  /* Prefix */
  prefix: string;
}

export class PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstruct extends Construct {
  public readonly stateMachineObj: sfn.IStateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: PieriandxLaunchInformaticsjobCreationStepFunctionsStateMachineConstructProps
  ) {
    super(scope, id);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'pieriandx_launch_step_functions_state_machine',
      {
        // stateMachineName
        stateMachineName: `${props.prefix}-sub-job-sfn`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          props.launchPieriandxInformaticsjobCreationStepfunctionTemplate
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          __generate_informaticsjob_lambda_function_arn__:
            props.generateInformaticsjobLambdaObj.currentVersion.functionArn,
          __table_name__: props.dynamodbTableObj.tableName,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    props.generateInformaticsjobLambdaObj.currentVersion.grantInvoke(stateMachine);

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine.role);

    // Set outputs
    this.stateMachineObj = stateMachine;
  }
}
