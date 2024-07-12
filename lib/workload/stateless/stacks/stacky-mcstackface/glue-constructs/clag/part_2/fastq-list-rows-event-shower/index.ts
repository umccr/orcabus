/*

Generate a suite of events for the new fastq list rows in the database

Hit the metadata manager to find the library ids, subject ids affected by the new fastq list rows

Launch an event for every subject, library and library run for the new fastq list rows

*/

import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import path from 'path';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../components/python-lambda-b64gz-translator';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';

export interface NewFastqListRowsEventShowerConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class NewFastqListRowsEventShowerConstruct extends Construct {
  public readonly newFastqListRowsEventShowerMap = {
    // General
    prefix: 'newFastqListRowsEventShower',
    // Tables
    tablePartition: 'fastqlistrows_by_instrument_run',
    // Set Event Triggers
    triggerSource: 'orcabus.workflowmanager',
    triggerStatus: 'succeeded',
    triggerDetailType: 'WorkflowRunStateChange',
    triggerWorkflowName: 'bsshFastqCopy',
    // Set Event Outputs
    outputSource: 'orcabus.instrumentrunmanager',
    outputStatus: {
      startEventShower: 'FastqListRowEventShowerStarting',
      completeEventShower: 'FastqListRowEventShowerComplete',
      newFastqListRow: 'newFastqListRow',
    },
    outputDetailType: {
      showerTerminal: 'FastqListRowShowerStateChange',
      fastqListRowStateChange: 'FastqListRowStateChange',
    },
    outputPayloadVersion: '0.1.0',
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: NewFastqListRowsEventShowerConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the lambdas
    */
    // The decompression fastq list row lambda
    const decompressFastqListRowLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.newFastqListRowsEventShowerMap.prefix,
      }
    ).lambdaObj;

    // Generate Data Objects
    // Translate the libraryrunstatechange event
    const generateEventDataObjsLambda = new PythonFunction(
      this,
      'generate_event_data_objects_lambda',
      {
        entry: path.join(__dirname, 'lambdas', 'generate_event_data_objects_py'),
        index: 'generate_event_data_objects.py',
        handler: 'handler',
        runtime: Runtime.PYTHON_3_12,
        architecture: Architecture.ARM_64,
      }
    );

    /*
    Part 2: Build state machine
    */

    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_fastq_list_row_sfn', {
      stateMachineName: `${this.newFastqListRowsEventShowerMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'fastq_list_row_event_shower_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        /* Generate Event Configurations */
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.newFastqListRowsEventShowerMap.outputSource,

        /* Specific event settings */
        // Event Shower Starting
        __fastq_list_row_transfer_starting_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.showerTerminal,
        __fastq_list_row_transfer_starting_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_list_row_transfer_starting_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.startEventShower,

        // New Fastq List Row
        __fastq_pair_added_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.fastqListRowStateChange,
        __fastq_pair_added_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_pair_added_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.newFastqListRow,

        // Event Shower Complete
        __fastq_list_row_transfer_complete_detail_type__:
          this.newFastqListRowsEventShowerMap.outputDetailType.showerTerminal,
        __fastq_list_row_transfer_complete_payload_version__:
          this.newFastqListRowsEventShowerMap.outputPayloadVersion,
        __fastq_list_row_transfer_complete_status__:
          this.newFastqListRowsEventShowerMap.outputStatus.completeEventShower,

        /* Table settings */
        __table_name__: props.tableObj.tableName,
        __table_partition_name__: this.newFastqListRowsEventShowerMap.tablePartition,

        /* Lambda functions */
        __decompress_fastq_list_rows_lambda_function_arn__:
          decompressFastqListRowLambda.currentVersion.functionArn,
        __generate_event_maps_lambda_function_arn__:
          generateEventDataObjsLambda.currentVersion.functionArn,
      },
    });

    /*
    Part 3: Wire up permissions
    */
    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    [decompressFastqListRowLambda, generateEventDataObjsLambda].forEach((lambda) => {
      lambda.currentVersion.grantInvoke(this.stateMachineObj.role);
    });

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /*
    Part 4: Build event rule
    */
    const eventRule = new events.Rule(this, 'update_database_on_new_fastqlistrows_event_rule', {
      ruleName: `stacky-${this.newFastqListRowsEventShowerMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.newFastqListRowsEventShowerMap.triggerSource],
        detailType: [this.newFastqListRowsEventShowerMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.newFastqListRowsEventShowerMap.triggerStatus }],
          workflowName: [
            {
              'equals-ignore-case': this.newFastqListRowsEventShowerMap.triggerWorkflowName,
            },
          ],
        },
      },
    });

    eventRule.addTarget(
      new eventsTargets.SfnStateMachine(this.stateMachineObj, {
        input: events.RuleTargetInput.fromEventPath('$.detail'),
      })
    );
  }
}
