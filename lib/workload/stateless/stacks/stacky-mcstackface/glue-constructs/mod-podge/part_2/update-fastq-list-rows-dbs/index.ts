import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 2

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `newFastqListRow`

* Populate the fastq list row attributes for the rgid for this workflow
*/

export interface WtsPopulateFastqListRowDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WtsPopulateFastqListRowConstruct extends Construct {
  public readonly WtsPopulateFastqListRowDbRowMap = {
    prefix: 'modpodge-update-fqlr',
    tablePartition: 'fastq_list_row',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'newFastqListRow',
    triggerDetailType: 'FastqListRowStateChange',
  };

  constructor(scope: Construct, id: string, props: WtsPopulateFastqListRowDbRowConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'update_fastq-list-row_db_row', {
      stateMachineName: `${this.WtsPopulateFastqListRowDbRowMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'add_fastq_list_rows_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition_name__: this.WtsPopulateFastqListRowDbRowMap.tablePartition,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the event bus for this event type
    */
    const rule = new events.Rule(this, 'wts_populate_fastq_list_row', {
      ruleName: `stacky-${this.WtsPopulateFastqListRowDbRowMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WtsPopulateFastqListRowDbRowMap.triggerSource],
        detailType: [this.WtsPopulateFastqListRowDbRowMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WtsPopulateFastqListRowDbRowMap.triggerStatus }],
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
