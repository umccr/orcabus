import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

interface PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  /* Lambdas paths */
  uploadDataToS3LambdaObj: PythonFunction;
  generateSamplesheetLambdaObj: PythonFunction;
  generateSequencerrunLambdaObj: PythonFunction;
  /* Step function templates */
  launchPieriandxSequencerrunCreationStepfunctionTemplate: string; // __dirname + '/../../../step_functions_templates/launch_pieriandx_sequencerrun_creation.asl.json'
  /* Custom props */
  prefix: string;
}

export class PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstruct extends Construct {
  public readonly stateMachineObj: sfn.IStateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: PieriandxLaunchSequencerrunCreationStepFunctionsStateMachineConstructProps
  ) {
    super(scope, id);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'pieriandx_launch_step_functions_state_machine',
      {
        // stateMachineName
        stateMachineName: `${props.prefix}-sub-sqrrun-sfn`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          props.launchPieriandxSequencerrunCreationStepfunctionTemplate
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          __upload_data_to_s3_lambda_function_arn__:
            props.uploadDataToS3LambdaObj.currentVersion.functionArn,
          __generate_samplesheet_lambda_function_arn__:
            props.generateSamplesheetLambdaObj.currentVersion.functionArn,
          __generate_sequencerrun_case_lambda_function_arn__:
            props.generateSequencerrunLambdaObj.currentVersion.functionArn,
          __table_name__: props.dynamodbTableObj.tableName,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    [
      props.uploadDataToS3LambdaObj,
      props.generateSamplesheetLambdaObj,
      props.generateSequencerrunLambdaObj,
    ].forEach((lambda_obj) => {
      lambda_obj.currentVersion.grantInvoke(stateMachine);
    });

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine);

    // Set outputs
    this.stateMachineObj = stateMachine;
  }
}
