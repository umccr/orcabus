import * as cdk from 'aws-cdk-lib';
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

interface PieriandxLaunchCaseCreationStepFunctionConstructProps {
  /* Stack Objects */
  dynamodbTableObj: dynamodb.ITableV2;
  /* Lambdas paths */
  generateCaseLambdaObj: PythonFunction;
  /* Step function templates */
  launchPieriandxCaseCreationStepfunctionTemplatePath: string;
  /* Custom */
  prefix: string;
}

export class PieriandxLaunchCaseCreationStepFunctionStateMachineConstruct extends Construct {
  public readonly stateMachineObj: sfn.IStateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: PieriandxLaunchCaseCreationStepFunctionConstructProps
  ) {
    super(scope, id);

    // Specify the statemachine and replace the arn placeholders with the lambda arns defined above
    const stateMachine = new sfn.StateMachine(
      this,
      'pieriandx_launch_step_functions_state_machine',
      {
        // stateMachineName
        stateMachineName: `${props.prefix}-sub-case-sfn`,
        // defintiontemplate
        definitionBody: DefinitionBody.fromFile(
          props.launchPieriandxCaseCreationStepfunctionTemplatePath
        ),
        // definitionSubstitutions
        definitionSubstitutions: {
          /* Tables */
          __table_name__: props.dynamodbTableObj.tableName,
          /* Lambdas */
          __generate_case_lambda_function_arn__:
            props.generateCaseLambdaObj.currentVersion.functionArn,
        },
      }
    );

    // Grant lambda invoke permissions to the state machine
    props.generateCaseLambdaObj.currentVersion.grantInvoke(stateMachine);

    // Allow state machine to read/write to dynamodb table
    props.dynamodbTableObj.grantReadWriteData(stateMachine);

    // Set outputs
    this.stateMachineObj = stateMachine;
  }
}
