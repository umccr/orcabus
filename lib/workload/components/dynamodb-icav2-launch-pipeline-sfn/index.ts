import { Construct } from 'constructs';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { Duration } from 'aws-cdk-lib';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { DefinitionBody } from 'aws-cdk-lib/aws-stepfunctions';

export interface SfnIcav2LaunchPipelineConstructProps {
  icav2AccessTokenSecretObj: secretsmanager.ISecret;
  tableObj: dynamodb.ITableV2;
  stateMachineName: string;
}

export class SfnIcav2LaunchPipelineConstruct extends Construct {
  public readonly lambdaObj: lambda_python.PythonFunction;
  public readonly stateMachine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: SfnIcav2LaunchPipelineConstructProps) {
    super(scope, id);

    // Create lambda object
    this.lambdaObj = new lambda_python.PythonFunction(this, 'icav2_cwl_launch_python_function', {
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      entry: path.join(__dirname, 'icav2_launch_pipeline_lambda_py'),
      index: 'icav2_launch_pipeline_lambda.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(20),
      environment: {
        ICAV2_ACCESS_TOKEN_SECRET_ID: props.icav2AccessTokenSecretObj.secretArn,
      },
    });

    // Grant read access
    props.icav2AccessTokenSecretObj.grantRead(<iam.IRole>this.lambdaObj.role);

    // Generate the state machine
    this.stateMachine = new sfn.StateMachine(this, 'icav2_launch_pipeline_state_machine', {
      // Name
      stateMachineName: props.stateMachineName,
      // Template
      definitionBody: DefinitionBody.fromFile(
        path.join(__dirname, 'step_functions_templates/icav2_launch_pipeline_sfn_template.asl.json')
      ),
      // Substitutions
      definitionSubstitutions: {
        /* Lambda arns */
        __launch_icav2_pipeline_lambda_function_name__: this.lambdaObj.functionName,
        /* Dynamodb tables */
        __table_name__: props.tableObj.tableName,
      },
    });

    // Grant read/write access to the dynamodb table
    props.tableObj.grantReadWriteData(<iam.IRole>this.stateMachine.role);
  }
}
