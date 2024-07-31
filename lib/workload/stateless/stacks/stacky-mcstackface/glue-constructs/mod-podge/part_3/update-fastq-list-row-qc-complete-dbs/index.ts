import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 3

Input Event Source: `orcabus.wgtsqcinputeventglue`
Input Event DetailType: `FastqListRowStateChange`
Input Event status: `QcComplete`

* Populate the fastq list row attributes for the rgid for this workflow
*/

export interface WtsFastqListRowQcCompleteDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WtsFastqListRowQcCompleteConstruct extends Construct {
  public readonly WtsFastqListRowQcCompleteDbRowMap = {
    prefix: 'modpodge-fqlr-qc-complete',
    tablePartition: 'fastq_list_row',
    triggerSource: 'orcabus.wgtsqcinputeventglue',
    triggerStatus: 'QcComplete',
    triggerDetailType: 'FastqListRowStateChange',
  };

  constructor(scope: Construct, id: string, props: WtsFastqListRowQcCompleteDbRowConstructProps) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'fastq_list_row_qc_complete', {
      stateMachineName: `${this.WtsFastqListRowQcCompleteDbRowMap.prefix}-sfn`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'add_fastq_list_row_qc_complete_to_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __fastq_list_row_partition_name__: this.WtsFastqListRowQcCompleteDbRowMap.tablePartition,
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
      ruleName: `stacky-${this.WtsFastqListRowQcCompleteDbRowMap.prefix}-event-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WtsFastqListRowQcCompleteDbRowMap.triggerSource],
        detailType: [this.WtsFastqListRowQcCompleteDbRowMap.triggerDetailType],
        detail: {
          status: [{ 'equals-ignore-case': this.WtsFastqListRowQcCompleteDbRowMap.triggerStatus }],
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
