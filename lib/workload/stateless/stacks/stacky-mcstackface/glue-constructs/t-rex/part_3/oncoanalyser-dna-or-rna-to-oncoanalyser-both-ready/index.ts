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
import { GetMetadataLambdaConstruct } from '../../../../../../../components/python-lambda-metadata-mapper';

export interface OncoanalyserDnaRnaReadyConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;
  /* Tables */
  tableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
}

export class OncoanalyserDnaRnaReadyConstruct extends Construct {
  public readonly OncoanalyserDnaRnaReadyMap = {
    prefix: 'trex-oncoanalyser-wgts-dna-rna',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerWorkflowNames: {
      DNA: 'oncoanalyser-wgts-dna',
      RNA: 'rnadna',
    },
    triggerDetailType: 'WorkflowRunStateChange',
    outputSource: 'orcabus.oncoanalyserinputeventglue',
    payloadVersion: '2024.07.23',
    workflowName: 'oncoanalyser-both',
    workflowVersion: '1.0.0',
    tablePartitionName: 'library',
  };

  constructor(scope: Construct, id: string, props: OncoanalyserDnaRnaReadyConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(
      this,
      'get_oncoanalyser_dna_rna_payload_py',
      {
        entry: path.join(__dirname, 'lambdas', 'get_oncoanalyser_dna_rna_payload_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_oncoanalyser_dna_rna_payload.py',
        handler: 'handler',
        memorySize: 1024,
      }
    );

    const getComplementLibraryPairLambdaObj = new PythonFunction(
      this,
      'get_complement_library_pair_lambdaobj',
      {
        entry: path.join(__dirname, 'lambdas', 'get_oncoanalyser_dna_rna_payload_py'),
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.ARM_64,
        index: 'get_oncoanalyser_dna_rna_payload.py',
        handler: 'handler',
        memorySize: 1024,
      }
    );
    const collectOrcaBusObjFromSubjectIdLambdaObj = new GetMetadataLambdaConstruct(
      this,
      'get_orcabus_id_from_subject_id',
      {
        functionNamePrefix: this.OncoanalyserDnaRnaReadyMap.prefix,
      }
    ).lambdaObj;

    // Add CONTEXT, FROM_ID and RETURN_STR environment variables to the lambda
    collectOrcaBusObjFromSubjectIdLambdaObj.addEnvironment('CONTEXT', 'subject');
    collectOrcaBusObjFromSubjectIdLambdaObj.addEnvironment('FROM_ID', '');
    collectOrcaBusObjFromSubjectIdLambdaObj.addEnvironment('RETURN_OBJ', '');

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.OncoanalyserDnaRnaReadyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.OncoanalyserDnaRnaReadyMap.prefix,
        workflowName: this.OncoanalyserDnaRnaReadyMap.workflowName,
        workflowVersion: this.OncoanalyserDnaRnaReadyMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'tn_complete_to_oa_dna_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.OncoanalyserDnaRnaReadyMap.outputSource,
        payloadVersion: this.OncoanalyserDnaRnaReadyMap.payloadVersion,
        workflowName: this.OncoanalyserDnaRnaReadyMap.workflowName,
        workflowVersion: this.OncoanalyserDnaRnaReadyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Prefixes */
        lambdaPrefix: this.OncoanalyserDnaRnaReadyMap.prefix,
        stateMachinePrefix: this.OncoanalyserDnaRnaReadyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const dnaCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'oncoanalyser_dna_complete_draft_sfn',
      {
        stateMachineName: `${this.OncoanalyserDnaRnaReadyMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'oncoanalyser_dna_or_rna_complete_to_oncoanalyser_both_ready_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Lambdas */
          __generate_draft_event_payload_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,
          __get_complement_library_pair_lambda_function_arn__:
            getComplementLibraryPairLambdaObj.currentVersion.functionArn,
          __get_orcabus_obj_from_subject_id_lambda_function_arn__:
            collectOrcaBusObjFromSubjectIdLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,

          /* Table Partitions */
          __library_partition_name__: this.OncoanalyserDnaRnaReadyMap.tablePartitionName,

          // State Machines
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,

          /* Miscell */
          __rna_workflow_run_name__: this.OncoanalyserDnaRnaReadyMap.triggerWorkflowNames.RNA,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(dnaCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    [
      generateEventDataLambdaObj,
      getComplementLibraryPairLambdaObj,
      collectOrcaBusObjFromSubjectIdLambdaObj,
    ].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(dnaCompleteToDraftSfn);
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
    // Allow the state machine to be able to invoke the preamble sfn
    sfnPreamble.grantStartExecution(dnaCompleteToDraftSfn);
    engineParameterAndReadyEventMakerSfn.grantStartExecution(dnaCompleteToDraftSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'oncoanalyser_dna_complete_to_sash_ready_rule', {
      ruleName: `stacky-${this.OncoanalyserDnaRnaReadyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.OncoanalyserDnaRnaReadyMap.triggerSource],
        detailType: [this.OncoanalyserDnaRnaReadyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.OncoanalyserDnaRnaReadyMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.OncoanalyserDnaRnaReadyMap.triggerWorkflowNames.DNA,
            },
            {
              'equals-ignore-case': this.OncoanalyserDnaRnaReadyMap.triggerWorkflowNames.RNA,
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
