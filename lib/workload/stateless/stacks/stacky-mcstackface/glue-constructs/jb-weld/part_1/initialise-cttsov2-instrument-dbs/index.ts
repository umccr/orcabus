import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import path from 'path';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import { WorkflowRunStateChangeInternalInputMakerConstruct } from '../../../../../../../components/event-workflowrunstatechange-internal-to-inputmaker-sfn';

/*
Part 1

Input Event Source: `orcabus.instrumentrunmanager`
Input Event DetailType: `SamplesheetShowerStateChange`
Input Event status: `SamplesheetRegisteredEventShowerStarting`

* Initialise cttsov2 instrument db construct
*/

export interface Cttsov2InitialiseInstrumentRunDbRowConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class Cttsov2InitialiseInstrumentRunDbRowConstruct extends Construct {
  public readonly Cttsov2InitialiseInstrumentRunDbRowMap = {
    prefix: 'cttsov2InitialiseInstrumentRunDbRow',
    tablePartition: 'instrument_run',
    triggerSource: 'orcabus.instrumentrunmanager',
    triggerStatus: 'SamplesheetRegisteredEventShowerStarting',
    triggerDetailType: 'SamplesheetShowerStateChange',
  };

  constructor(
    scope: Construct,
    id: string,
    props: Cttsov2InitialiseInstrumentRunDbRowConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build the internal sfn
    */
    const inputMakerSfn = new sfn.StateMachine(this, 'initialise_instrument_run_db_row', {
      stateMachineName: `${this.Cttsov2InitialiseInstrumentRunDbRowMap.prefix}-initialise-run-db-row`,
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'initialise_cttsov2_instrument_run_db_sfn_template.asl.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __instrument_run_partition_name__:
          this.Cttsov2InitialiseInstrumentRunDbRowMap.tablePartition,
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
    // TODO
  }
}
