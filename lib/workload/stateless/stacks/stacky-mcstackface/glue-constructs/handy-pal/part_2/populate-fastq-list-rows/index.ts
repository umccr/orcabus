/*

Populate WTS fastq list rows from the fastq list row showers

*/

import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

export interface OncoanalyserPopulateFastqListRowRunDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class OncoanalyserPopulateFastqListRowConstruct extends Construct {
  public readonly OncoanalyserPopulateFastqListRowRunDbRowMap = {
    prefix: 'handypal-populate-fqlr-row',
    tablePartition: 'fastq_list_row',
    triggerSource: 'orcabus.fastqglue',
    triggerStatus: 'newFastqListRow',
    triggerDetailType: 'StackyFastqListRowStateChange',
  };

  constructor(
    scope: Construct,
    id: string,
    props: OncoanalyserPopulateFastqListRowRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_fastq-list-row_db_row', {
      stateMachineName: `${this.OncoanalyserPopulateFastqListRowRunDbRowMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'populate_fastq_list_rows_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition_name__:
          this.OncoanalyserPopulateFastqListRowRunDbRowMap.tablePartition,
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
    const rule = new events.Rule(this, 'oncoanalyser_populate_fastq_list_row', {
      ruleName: `stacky-${this.OncoanalyserPopulateFastqListRowRunDbRowMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.OncoanalyserPopulateFastqListRowRunDbRowMap.triggerSource],
        detailType: [this.OncoanalyserPopulateFastqListRowRunDbRowMap.triggerDetailType],
        detail: {
          status: [
            {
              'equals-ignore-case': this.OncoanalyserPopulateFastqListRowRunDbRowMap.triggerStatus,
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
