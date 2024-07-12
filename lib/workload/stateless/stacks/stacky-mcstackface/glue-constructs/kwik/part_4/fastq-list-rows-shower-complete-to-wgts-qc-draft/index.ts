import { Construct } from 'constructs';
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

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `FastqListRowEventShowerComplete`

Output Event source: `orcabus.wgtsinputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Trigger wgts events collecting all wgts in the run
*/

export interface WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps {
  workflowsTableObj: dynamodb.ITableV2;
  wgtsQcGlueTableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WgtsQcFastqListRowShowerCompleteToWorkflowDraftConstruct extends Construct {
  public readonly WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap = {
    /* General settings */
    prefix: 'wgtsQcFastqListRowShowerCompleteToWorkflowDraftRun',
    /* Table Partition Settings */
    wgtsGlueTablePartition: {
      instrumentRun: 'instrument_run',
      library: 'library',
      fastqListRow: 'fastq_list_row',
    },
    portalRunPartitionName: 'portal_run',
    /* Input Event Settings */
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'FastqListRowEventShowerComplete',
    triggerDetailType: 'FastqListRowShowerStateChange',
    /* Output Event Settings */
    outputSource: 'orcabus.wgtsqcinputeventglue',
    outputStatus: 'draft',
    outputDetailType: 'WorkflowDraftRunStateChange',
    /* Payload version */
    payloadVersion: '0.1.0',
    /* Workflow settings */
    workflowName: 'wgtsQc',
    workflowVersion: '4.2.4',
  };

  constructor(
    scope: Construct,
    id: string,
    props: WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Generate the preamble (sfn to generate the portal run id and the workflow run name)
    */
    const sfn_preamble = new WorkflowDraftRunStateChangeCommonPreambleConstruct(
      this,
      `${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}_sfn_preamble`,
      {
        portalRunTablePartitionName:
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.portalRunPartitionName,
        stateMachinePrefix: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix,
        tableObj: props.workflowsTableObj,
        workflowName: this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
        workflowVersion:
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,
      }
    ).stepFunctionObj;

    /*
    Part 1: Build the lambdas
    */
    const generateEventDataLambdaObj = new PythonFunction(this, 'generate_event_data', {
      entry: path.join(__dirname, 'lambdas', 'generate_event_data_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'generate_event_data.py',
      handler: 'handler',
      memorySize: 1024,
    });

    /*
    Part 2: Build the sfn
    */
    const inputMakerSfn = new sfn.StateMachine(
      this,
      'fastq_list_row_complete_to_workflow_draft_run_events',
      {
        stateMachineName: `${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_functions_templates',
            'fastq_list_row_shower_complete_event_to_wgts_qc_draft_events_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* General Settings */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __table_name__: props.wgtsQcGlueTableObj.tableName,

          /* Table partitions */
          __fastq_list_row_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.wgtsGlueTablePartition
              .fastqListRow,
          __instrument_run_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.wgtsGlueTablePartition
              .instrumentRun,
          __library_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.wgtsGlueTablePartition
              .library,
          __portal_run_partition_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.portalRunPartitionName,
          /* Output event settings */
          // Event detail
          __event_source__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputSource,
          __detail_type__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputDetailType,
          __output_status__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputStatus,
          __payload_version__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.payloadVersion,
          // Workflow detail
          __workflow_name__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
          __workflow_version__:
            this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

          /* Lambdas */
          __generate_wgts_draft_event_data_lambda_function_arn__:
            generateEventDataLambdaObj.currentVersion.functionArn,
        },
      }
    );

    /*
    Part 3: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.wgtsQcGlueTableObj.grantReadWriteData(inputMakerSfn.role);

    // Allow the sfn to invoke the lambda
    generateEventDataLambdaObj.currentVersion.grantInvoke(inputMakerSfn.role);

    // Allow the sfn to submit events to the event bus
    props.eventBusObj.grantPutEventsTo(inputMakerSfn.role);

    //

    /*
    Part 4: Subscribe to the event bus for this event type
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_fastq_list_row_shower_complete', {
      ruleName: `stacky-${this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerSource],
        detailType: [
          this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerDetailType,
        ],
        detail: {
          status: [
            {
              'equals-ignore-case':
                this.WgtsQcFastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerStatus,
            },
          ],
        },
      },
    });

    // Add target of event to be the state machine
    rule.addTarget(
      new eventsTargets.SfnStateMachine(inputMakerSfn, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
