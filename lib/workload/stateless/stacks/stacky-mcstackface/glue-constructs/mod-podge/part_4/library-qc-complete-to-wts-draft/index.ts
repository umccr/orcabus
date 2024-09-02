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
import { WorkflowDraftRunStateChangeCommonPreambleConstruct } from '../../../../../../../components/sfn-workflowdraftrunstatechange-common-preamble';

/*
Part 4

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `LibraryStateChange`
Input Event status: `QcComplete`

Output Event Source: `orcabus.wtsinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Subscribe to the wgts input event glue, library complete event.
* Launch a draft event for the wts pipeline if the libraries' subject has a complement library that is also complete
*/

export interface LibraryQcCompleteToWtsDraftConstructProps {
  eventBusObj: events.IEventBus;
  tableObj: dynamodb.ITableV2;
  workflowsTableObj: dynamodb.ITableV2;
}

export class LibraryQcCompleteToWtsDraftConstruct extends Construct {
  public readonly WtsDraftMap = {
    prefix: 'modpodge-library-qc-to-wts',
    tablePartition: {
      library: 'library',
      fastq_list_row: 'fastq_list_row',
    },
    portalRunPartitionName: 'portal_run',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QC_COMPLETE',
    triggerDetailType: 'LibraryStateChange',
    outputSource: 'orcabus.wtsinputeventglue',
    outputDetailType: 'WorkflowDraftRunStateChange',
    outputStatus: 'DRAFT',
    payloadVersion: '2024.07.23',
    workflowName: 'wts',
    workflowVersion: '4.2.4',
  };

  constructor(scope: Construct, id: string, props: LibraryQcCompleteToWtsDraftConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // Generate event data lambda object
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_draft_event_payload_py', {
      entry: path.join(__dirname, 'lambdas', 'generate_draft_event_payload_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_draft_event_payload.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.WtsDraftMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName: this.WtsDraftMap.portalRunPartitionName,
        stateMachinePrefix: this.WtsDraftMap.prefix,
        tableObj: props.workflowsTableObj,
        workflowName: this.WtsDraftMap.workflowName,
        workflowVersion: this.WtsDraftMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 2: Build the sfn
    */
    const qcCompleteToDraftSfn = new sfn.StateMachine(
      this,
      'library_qc_complete_sfn_to_wts_draft',
      {
        stateMachineName: `${this.WtsDraftMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'add_library_qc_complete_to_wts_draft_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* Events */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __event_source__: this.WtsDraftMap.outputSource,
          __detail_type__: this.WtsDraftMap.outputDetailType,
          __output_status__: this.WtsDraftMap.outputStatus,
          __payload_version__: this.WtsDraftMap.payloadVersion,
          __workflow_name__: this.WtsDraftMap.workflowName,
          __workflow_version__: this.WtsDraftMap.workflowVersion,

          /* Lambdas */
          __generate_draft_event_payload_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,

          /* Tables */
          __table_name__: props.tableObj.tableName,
          __library_partition_name__: this.WtsDraftMap.tablePartition.library,
          __fastq_list_row_partition_name__: this.WtsDraftMap.tablePartition.fastq_list_row,

          // State Machines
          __sfn_preamble_state_machine_arn__: sfn_preamble.stateMachineArn,
        },
      }
    );

    /*
    Part 2: Grant the sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(qcCompleteToDraftSfn);

    // allow the step function to submit events
    props.eventBusObj.grantPutEventsTo(qcCompleteToDraftSfn);

    // allow the step function to invoke the lambdas
    generateEventDataLambdaObj.currentVersion.grantInvoke(qcCompleteToDraftSfn);

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
    // Allow the state machine to be able to invoke the preamble sfn
    sfn_preamble.grantStartExecution(qcCompleteToDraftSfn);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'library_qc_complete_to_tn_draft', {
      ruleName: `stacky-${this.WtsDraftMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WtsDraftMap.triggerSource],
        detailType: [this.WtsDraftMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WtsDraftMap.triggerStatus }],
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
