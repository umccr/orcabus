/*
Generate a ready event for the oncoanalyser workflow.

Subscribe to library qc complete for the rna library.

Subscribe to tn complete for the dna libraries.
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
import { NagSuppressions } from 'cdk-nag';

/*
Part 3

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: LibraryStateChange
Input Event status: `QC_COMPLETE`

OR

Input Event Source: `orcabus.workflowmanager`
Input Event DetailType: `WorkflowRunStateChange`
Input Event WorkflowName: tumor-normal
Input Event status: `SUCCEEDED`

Output Event Source: `orcabus.oncoanlyserinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `READY`

* Subscribe to the workflow manager succeeded event for tumor normal libraries.
* Launch a draft event for the umccrise pipeline
*/

export interface OncoanalyserDnaOrRnaReadyConstructProps {
  /* Events */
  eventBusObj: events.IEventBus;
  /* Tables */
  tableObj: dynamodb.ITableV2;
  /* SSM Parameters */
  outputUriSsmParameterObj: ssm.IStringParameter;
  logsUriSsmParameterObj: ssm.IStringParameter;
  cacheUriSsmParameterObj: ssm.IStringParameter;
}

export class OncoanalyserDnaOrRnaReadyConstruct extends Construct {
  public readonly OncoanalyserReadyMap = {
    outputSource: 'orcabus.oncoanalyserglue',
    payloadVersion: '2024.07.23',
    tablePartitionName: {
      library: 'library',
      fastqListRow: 'fastq_list_row',
    },
  };

  public readonly DnaOnlyMap = {
    prefix: 'handypal-tn-to-oa-wgts-dna',
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'SUCCEEDED',
    triggerWorkflowName: 'tumor-normal',
    triggerDetailType: 'WorkflowRunStateChange',
    workflowName: 'oncoanalyser-wgts-dna',
    workflowVersion: '2.0.0',
  };

  public readonly RnaOnlyMap = {
    prefix: 'handypal-libraryqc-to-oa-rna',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'LibraryStateChange',
    sampleType: 'WTS',
    workflowName: 'oncoanalyser-wgts-rna',
    workflowVersion: '2.0.0',
  };

  constructor(scope: Construct, id: string, props: OncoanalyserDnaOrRnaReadyConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the DNA stack
    */
    this.build_dna_object(props);

    /*
    Part 2: Build the RNA stack
    */
    this.build_rna_object(props);
  }

  // Create a function here to build the dna object
  private build_dna_object(props: OncoanalyserDnaOrRnaReadyConstructProps) {
    /*
    Part 1 Build the lambdas
    */
    const generateDnaEventLambdaObj = new PythonFunction(this, 'generate_dna_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_dna_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_dna_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.DnaOnlyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.DnaOnlyMap.prefix,
        workflowName: this.DnaOnlyMap.workflowName,
        workflowVersion: this.DnaOnlyMap.workflowVersion,
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
        outputSource: this.OncoanalyserReadyMap.outputSource,
        payloadVersion: this.OncoanalyserReadyMap.payloadVersion,
        workflowName: this.DnaOnlyMap.workflowName,
        workflowVersion: this.DnaOnlyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Prefixes */
        lambdaPrefix: this.DnaOnlyMap.prefix,
        stateMachinePrefix: this.DnaOnlyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const tnCompleteToOncoDraftSfn = new sfn.StateMachine(this, 'tn_complete_to_onco_draft_sfn', {
      stateMachineName: `${this.DnaOnlyMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'tn_complete_to_oncoanalyser_dna_ready_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Lambdas */
        __generate_draft_event_payload_lambda_function_arn__:
          generateDnaEventLambdaObj.currentVersion.functionArn,

        /* Tables */
        __table_name__: props.tableObj.tableName,

        /* Table Partitions */
        __library_partition_name__: this.OncoanalyserReadyMap.tablePartitionName.library,

        // State Machines
        __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
        __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
      },
    });

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(tnCompleteToOncoDraftSfn);

    // allow the step function to invoke the lambdas
    generateDnaEventLambdaObj.currentVersion.grantInvoke(tnCompleteToOncoDraftSfn);

    // Allow the step function to call the preamble sfn
    [sfnPreamble, engineParameterAndReadyEventMakerSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(tnCompleteToOncoDraftSfn);
      sfnObj.grantRead(tnCompleteToOncoDraftSfn);
    });

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    tnCompleteToOncoDraftSfn.addToRolePolicy(
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
      tnCompleteToOncoDraftSfn,
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
    const rule = new events.Rule(this, 'tn_complete_to_umccrise_draft_rule', {
      ruleName: `stacky-${this.DnaOnlyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.DnaOnlyMap.triggerSource],
        detailType: [this.DnaOnlyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.DnaOnlyMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.DnaOnlyMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(tnCompleteToOncoDraftSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }

  private build_rna_object(props: OncoanalyserDnaOrRnaReadyConstructProps) {
    /*
    Part 1 Build the lambdas
    */
    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_rna_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_rna_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_rna_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    const collectOrcaBusIdLambdaObj = new GetMetadataLambdaConstruct(
      this,
      'get_orcabus_id_from_subject_id',
      {
        functionNamePrefix: this.RnaOnlyMap.prefix,
      }
    ).lambdaObj;

    // Add CONTEXT, FROM_ID and RETURN_STR environment variables to the lambda
    collectOrcaBusIdLambdaObj.addEnvironment('CONTEXT', 'subject');
    collectOrcaBusIdLambdaObj.addEnvironment('FROM_ORCABUS', '');
    collectOrcaBusIdLambdaObj.addEnvironment('RETURN_OBJ', '');

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfnPreamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.RnaOnlyMap.prefix}_sfn_preamble`,
      {
        stateMachinePrefix: this.RnaOnlyMap.prefix,
        workflowName: this.RnaOnlyMap.workflowName,
        workflowVersion: this.RnaOnlyMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the engine parameters sfn
    */
    const engineParameterAndReadyEventMakerSfn = new GenerateWorkflowRunStateChangeReadyConstruct(
      this,
      'fastqlistrow_complete_to_oa_rna_ready_submitter',
      {
        /* Event Placeholders */
        eventBusObj: props.eventBusObj,
        outputSource: this.OncoanalyserReadyMap.outputSource,
        payloadVersion: this.OncoanalyserReadyMap.payloadVersion,
        workflowName: this.RnaOnlyMap.workflowName,
        workflowVersion: this.RnaOnlyMap.workflowVersion,

        /* SSM Parameters */
        outputUriSsmParameterObj: props.outputUriSsmParameterObj,
        logsUriSsmParameterObj: props.logsUriSsmParameterObj,
        cacheUriSsmParameterObj: props.cacheUriSsmParameterObj,

        /* Prefixes */
        lambdaPrefix: this.RnaOnlyMap.prefix,
        stateMachinePrefix: this.RnaOnlyMap.prefix,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const qcCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'library_qc_complete_sfn_to_onco_rna_draft',
      {
        stateMachineName: `${this.RnaOnlyMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'library_wts_qc_complete_to_oncoanalyser_rna_ready_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Lambdas */
          __generate_draft_event_payload_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,
          __get_orcabus_obj_from_subject_id_lambda_function_arn__:
            collectOrcaBusIdLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,
          __library_partition_name__: this.OncoanalyserReadyMap.tablePartitionName.library,
          __fastq_list_row_partition_name__:
            this.OncoanalyserReadyMap.tablePartitionName.fastqListRow,
          __sample_type__: this.RnaOnlyMap.sampleType,

          /* State Machines */
          __sfn_preamble_state_machine_arn__: sfnPreamble.stateMachineArn,
          __launch_ready_event_sfn_arn__: engineParameterAndReadyEventMakerSfn.stateMachineArn,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    [generateEventDataLambdaObj, collectOrcaBusIdLambdaObj].forEach((lambdaObj) => {
      lambdaObj.currentVersion.grantInvoke(qcCompleteToDraftSfn);
    });

    // Allow the state machine to be able to invoke the preamble sfn
    [sfnPreamble, engineParameterAndReadyEventMakerSfn].forEach((sfnObj) => {
      sfnObj.grantStartExecution(qcCompleteToDraftSfn);
      sfnObj.grantRead(qcCompleteToDraftSfn);
    });

    /* Allow step function to call nested state machine */
    // Because we run a nested state machine, we need to add the permissions to the state machine role
    // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
    qcCompleteToDraftSfn.addToRolePolicy(
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
      qcCompleteToDraftSfn,
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
    const rule = new events.Rule(this, 'library_qc_complete_to_oncorna_draft', {
      ruleName: `stacky-${this.RnaOnlyMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.RnaOnlyMap.triggerSource],
        detailType: [this.RnaOnlyMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.RnaOnlyMap.triggerStatus }],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(qcCompleteToDraftSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
