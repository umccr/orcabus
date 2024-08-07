import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';

/*
Part 1

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `SamplesheetShowerStateChange`
Input Event status: `SamplesheetRegisteredEventShowerStarting`

* Initialise wgts instrument db construct
*/

export interface WgtsQcInitialiseInstrumentRunDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class WgtsQcInitialiseInstrumentRunDbRowConstruct extends Construct {
  public readonly WgtsQcInitialiseInstrumentRunDbRowMap = {
    prefix: 'kwik-make-instrument-run-row',
    tablePartition: 'instrument_run',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'SamplesheetRegisteredEventShowerStarting',
    triggerDetailType: 'SamplesheetShowerStateChange',
  };

  constructor(
    scope: Construct,
    id: string,
    props: WgtsQcInitialiseInstrumentRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_instrument_run_db_row', {
      stateMachineName: `${this.WgtsQcInitialiseInstrumentRunDbRowMap.prefix}-initialise-run-db-row`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_functions_templates',
          'initialise_wgts_instrument_run_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __instrument_run_partition_name__:
          this.WgtsQcInitialiseInstrumentRunDbRowMap.tablePartition,
      },
    });

    /*
    Part 2: Grant the internal sfn permissions
    */
    // access the dynamodb table
    props.tableObj.grantReadWriteData(inputMakerSfn.role);

    /*
    Part 3: Subscribe to the event bus and trigger the internal sfn
    */
    const rule = new events.Rule(this, 'wgts_subscribe_to_samplesheet_shower', {
      ruleName: `stacky-${this.WgtsQcInitialiseInstrumentRunDbRowMap.prefix}-rule`,
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.WgtsQcInitialiseInstrumentRunDbRowMap.triggerSource],
        detailType: [this.WgtsQcInitialiseInstrumentRunDbRowMap.triggerDetailType],
        detail: {
          status: [
            { 'equals-ignore-case': this.WgtsQcInitialiseInstrumentRunDbRowMap.triggerStatus },
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
