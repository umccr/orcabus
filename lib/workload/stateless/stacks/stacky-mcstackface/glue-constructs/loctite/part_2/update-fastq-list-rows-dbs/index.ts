import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 3

Input Event Source: `orcabus.fastqglue`
Input Event DetailType: `StackyFastqListRowStateChange`
Input Event status: `newFastqListRow`

* Populate the fastq list row attributes for the rgid for this workflow
*/

export interface TnPopulateFastqListRowDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class TnPopulateFastqListRowConstruct extends Construct {
  public readonly TnPopulateFastqListRowDbRowMap = {
    prefix: 'loctite-populate-fqlr-row',
    tablePartition: 'fastq_list_row',
    triggerSource: 'orcabus.fastqglue',
    triggerStatus: 'newFastqListRow',
    triggerDetailType: 'StackyFastqListRowStateChange',
  };

  constructor(scope: Construct, id: string, props: TnPopulateFastqListRowDbRowConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'update_fastq-list-row_db_row', {
      stateMachineName: `${this.TnPopulateFastqListRowDbRowMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'add_fastq_list_rows_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition_name__: this.TnPopulateFastqListRowDbRowMap.tablePartition,
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
    const rule = new events.Rule(this, 'tn_populate_fastq_list_row', {
      ruleName: `stacky-${this.TnPopulateFastqListRowDbRowMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.TnPopulateFastqListRowDbRowMap.triggerSource],
        detailType: [this.TnPopulateFastqListRowDbRowMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.TnPopulateFastqListRowDbRowMap.triggerStatus }],
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
