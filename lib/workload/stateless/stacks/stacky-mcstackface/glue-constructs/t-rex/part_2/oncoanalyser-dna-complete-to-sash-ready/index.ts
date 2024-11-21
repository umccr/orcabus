/*

Oncoanalyser dna complete to sash ready status

Given a oncoanalyser-wgts-dna complete event, generate a sash ready event for processing

*/

import { Construct } from 'constructs';
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';
import { GenerateWorkflowRunStateChangeReadyConstruct } from '../../../../../../../components/sfn-generate-workflowrunstatechange-ready-event';
import { NagSuppressions } from 'cdk-nag';

export interface OncoanalyserDnaToSashReadyConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;
  /* Tables */
  tableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
}

export class OncoanalyserDnaToSashReadyConstruct extends Construct {
  public readonly SashReadyMap = {
    prefix: 'trex-oncodna-complete-to-sash',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowName: 'oncoanalyser-wgts-dna',
    triggerDetailType: 'WorkflowRunStateChange',
    outputSource: 'orcabus.sashinputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'sash',
    workflowVersion: '1.0.0',
    tablePartitionName: 'library',
  };

  constructor(scope: Construct, id: string, props: OncoanalyserDnaToSashReadyConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_sash_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_sash_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_sash_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.SashReadyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.SashReadyMap.prefix,
        workflowName: this.SashReadyMap.workflowName,
        workflowVersion: this.SashReadyMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_wgtsqc_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.SashReadyMap.outputSource,
        payloadVersion: this.SashReadyMap.payloadVersion,
        workflowName: this.SashReadyMap.workflowName,
        workflowVersion: this.SashReadyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Prefixes */
        lambdaPrefix: this.SashReadyMap.prefix,
        stateMachinePrefix: this.SashReadyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const dnaCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'oncoanalyser_dna_complete_draft_sfn',
      {
        stateMachineName: `${this.SashReadyMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'oncoanalyser_dna_complete_to_sash_ready_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Lambdas */
          __generate_sash_payload_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,

          /* Table Partitions */
          __library_partition_name__: this.SashReadyMap.tablePartitionName,

          // State Machines
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(dnaCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    generateEventDataLambdaObj.currentVersion.grantInvoke(dnaCompleteToDraftSfn);

    // Allow the state machine to be able to invoke the preamble sfn
    [sfnPreamble, engineParameterAndReadyEventMakerSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(dnaCompleteToDraftSfn);
      sfnObj.grantRead(dnaCompleteToDraftSfn);
    });

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    dnaCompleteToDraftSfn.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
        ],
        actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
      })
    );

    // https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html#sync-async-iam-policies
    // Polling requires permission for states:DescribeExecution
    NagSuppressions.addResourceSuppressions(
      dnaCompleteToDraftSfn,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'grantRead uses asterisk at the end of executions, as we need permissions for all execution invocations',
        },
      ],
      true
    );

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'oncoanalyser_dna_complete_to_sash_ready_rule', {
      ruleName: `stacky-${this.SashReadyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.SashReadyMap.triggerSource],
        detailType: [this.SashReadyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.SashReadyMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.SashReadyMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(dnaCompleteToDraftSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
