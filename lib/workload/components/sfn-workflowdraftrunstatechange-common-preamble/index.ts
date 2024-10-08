/*
This sfn works as a subfunction with the primary aim of

1. Generating a portal run id and a workflow run name
2. Entering the portal run id and workflow run name into the portal run glue database
*/

import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import path from 'path';
import { Duration } from 'aws-cdk-lib';

export interface WorkflowRunStateChangeInternalInputMakerProps {
  /* Object name prefixes */
  stateMachinePrefix: string;
  /* Workflow metadata constants */
  workflowName: string;
  workflowVersion: string;
}

export class WorkflowDraftRunStateChangeCommonPreambleConstruct extends Construct {
  public readonly stepFunctionObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: WorkflowRunStateChangeInternalInputMakerProps) {
    super(scope, id);

    /*
    Part 1 - Generate the two lambdas required for the statemachine
    */

    /* Generate the portal run id name lambda */
    const portalRunIdLambda = new PythonFunction(this, 'generate_portal_run_id_lambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      entry: path.join(__dirname, 'lambdas', 'generate_portal_run_id_py'),
      index: 'generate_portal_run_id.py',
      handler: 'handler',
      memorySize: 1024,
      timeout: Duration.seconds(3),
    });

    /* Generate the workflow run name lambda */
    const workflowRunNameLambda = new PythonFunction(
      this,
      'generate_workflow_run_name_python_lambda',
      {
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        entry: path.join(__dirname, 'lambdas', 'generate_workflow_run_name_py'),
        index: 'generate_workflow_run_name.py',
        handler: 'handler',
        memorySize: 1024,
        timeout: Duration.seconds(3),
      }
    );

    /*
    Part 2 - Build the AWS State Machine
    */
    this.stepFunctionObj = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: `${props.stateMachinePrefix}-preamble-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'workflowdraftrunstatechange_preamble_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_portal_run_id_lambda_function_arn__:
          portalRunIdLambda.currentVersion.functionArn,
        __generate_workflow_run_name_lambda_function_arn__:
          workflowRunNameLambda.currentVersion.functionArn,
        /* Workflow name */
        __workflow_name__: props.workflowName,
        __workflow_version__: props.workflowVersion,
      },
    });

    /*
    Part 3 - Connect permissions
    */
    /* Allow step functions to invoke the lambda */
    [workflowRunNameLambda, portalRunIdLambda].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(<iam.IRole>this.stepFunctionObj.role);
    });
  }
}
