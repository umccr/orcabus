import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import * as lambda from 'aws-cdk-lib/aws-lambda';

/*
Part 4

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `FastqListRowEventShowerComplete`

Output Event source: `orcabus.cttsov2inputeventglue`
Output Event DetailType: `WorkflowDraftRunStateChange`
Output Event status: `draft`

* Trigger cttsov2 events collecting all cttsov2 in the run
*/

export interface Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class Cttsov2FastqListRowShowerCompleteToWorkflowDraftConstruct extends Construct {
  public readonly Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap = {
    /* General settings */
    prefix: 'cttsov2FastqListRowShowerCompleteToWorkflowDraftRun',
    /* Table Partition Settings */
    tablePartition: {
      instrumentRun: 'instrument_run',
      library: 'library',
      bclconvertData: 'bclconvert_data',
      fastqListRow: 'fastq_list_row',
    },
    /* Input Event Settings */
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'FastqListRowEventShowerComplete',
    triggerDetailType: 'FastqListRowShowerStateChange',
    /* Output Event Settings */
    outputSource: 'orcabus.cttsov2inputeventglue',
    outputStatus: 'draft',
    outputDetailType: 'WorkflowDraftRunStateChange',
    /* Payload version */
    payloadVersion: '0.1.0',
    /* Workflow settings */
    workflowName: 'cttsov2',
    workflowVersion: '2.5.0',
  };

  constructor(
    scope: Construct,
    id: string,
    props: Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    const buildCttsoV2Samplesheet = new PythonFunction(this, 'build_cttsov2_samplesheet', {
      entry: path.join(__dirname, 'lambdas', 'build_cttsov2_samplesheet_py'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'build_cttso_v2_samplesheet.py',
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
        stateMachineName: `${this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-sfn`,
        definitionBody: sfn.DefinitionBody.fromFile(
          path.join(
            __dirname,
            'step_function_templates',
            'fastq_list_row_shower_complete_event_to_cttsov2_draft_events_sfn_template.asl.json'
          )
        ),
        definitionSubstitutions: {
          /* General Settings */
          __event_bus_name__: props.eventBusObj.eventBusName,
          __table_name__: props.tableObj.tableName,

          /* Table partitions */
          __bclconvert_data_row_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.tablePartition
              .bclconvertData,
          __fastq_list_row_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.tablePartition
              .fastqListRow,
          __instrument_run_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.tablePartition
              .instrumentRun,
          __library_partition_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.tablePartition.library,

          /* Output event settings */
          // Event detail
          __event_source__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputSource,
          __detail_type__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputDetailType,
          __output_status__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.outputStatus,
          __payload_version__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.payloadVersion,
          // Workflow detail
          __workflow_name__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowName,
          __workflow_version__:
            this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.workflowVersion,

          /* Lambdas */
          __generate_samplesheet_lambda_function_arn__:
            buildCttsoV2Samplesheet.currentVersion.functionArn,
        },
      }
    );

    /*
    Part 3: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    // Allow the sfn to invoke the lambda
    buildCttsoV2Samplesheet.currentVersion.grantInvoke(inputMakerSfn.role);

    // Allow the sfn to submit events to the event bus
    props.eventBusObj.grantPutEventsTo(inputMakerSfn.role);

    /*
    Part 4: Subscribe to the event bus for this event type
    */
    const rule = new events.Rule(this, 'cttsov2_subscribe_to_fastq_list_row_shower_complete', {
      ruleName: `stacky-${this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerSource],
        detailType: [
          this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerDetailType,
        ],
        detail: {
          status: [
            {
              'equals-ignore-case':
                this.Cttsov2FastqListRowShowerCompleteToWorkflowDraftRunDbRowMap.triggerStatus,
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
