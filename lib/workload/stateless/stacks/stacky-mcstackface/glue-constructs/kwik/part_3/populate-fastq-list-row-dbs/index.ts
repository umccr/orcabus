import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 3

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `newFastqListRow`

* Populate the fastq list row attributes for the rgid for this workflow
*/

export interface WgtsQcPopulateFastqListRowRunDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WgtsQcPopulateFastqListRowConstruct extends Construct {
  public readonly WgtsQcPopulateFastqListRowRunDbRowMap = {
    prefix: 'wgtsQcPopulateFastqListRow',
    tablePartition: 'fastq_list_row',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'newFastqListRow',
    triggerDetailType: 'FastqListRowStateChange',
  };

  constructor(
    scope: Construct,
    id: string,
    props: WgtsQcPopulateFastqListRowRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_fastq-list-row_db_row', {
      stateMachineName: `${this.WgtsQcPopulateFastqListRowRunDbRowMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'update_fastq_list_row_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition_name__:
          this.WgtsQcPopulateFastqListRowRunDbRowMap.tablePartition,
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
    const rule = new events.Rule(this, 'wgts_populate_fastq_list_row', {
      ruleName: `stacky-${this.WgtsQcPopulateFastqListRowRunDbRowMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcPopulateFastqListRowRunDbRowMap.triggerSource],
        detailType: [this.WgtsQcPopulateFastqListRowRunDbRowMap.triggerDetailType],
        detail: {
          status: [
            { 'equals-ignore-case': this.WgtsQcPopulateFastqListRowRunDbRowMap.triggerStatus },
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
