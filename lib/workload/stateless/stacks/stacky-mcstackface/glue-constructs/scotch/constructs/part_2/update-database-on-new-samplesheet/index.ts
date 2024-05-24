import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import path from 'path';
import { LambdaB64GzTranslatorConstruct } from '../../../../../../../../components/lambda-b64gz-translator';

export interface updateDataBaseOnNewSamplesheetEventConstructProps {
  tableObj: dynamodb.ITableV2;
  eventBusObj: events.IEventBus;
}

export class updateDataBaseOnNewSamplesheetEventConstruct extends Construct {
  public declare updateDataBaseOnNewSamplesheetEventMap: {
    prefix: 'updateDatabaseOnNewSamplesheet';
    tablePartition: 'samplesheet_by_instrument_run';
    triggerSource: 'orcabus.workflowmanager';
    triggerStatus: 'succeeded';
    triggerDetailType: 'workflowRunStateChange';
    triggerWorkflowName: 'bclconvert';
    outputSource: 'orcabus.instrumentmanager';
    outputStatus: 'succeeded';
    outputDetailType: 'instrumentRunStateChange';
  };

  public readonly stateMachineObj: sfn.StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: updateDataBaseOnNewSamplesheetEventConstructProps
  ) {
    super(scope, id);

    /*
    Part 1: Build decompression lambda
    */
    const decompressSamplesheetLambda = new LambdaB64GzTranslatorConstruct(
      this,
      'lambda_b64gz_translator_lambda',
      {
        functionNamePrefix: this.updateDataBaseOnNewSamplesheetEventMap.prefix,
      }
    ).lambdaObj;

    /*
    Part 2: Build state machine
    */
    this.stateMachineObj = new sfn.StateMachine(this, 'update_database_on_new_samplesheet_sfn', {
      definitionBody: sfn.DefinitionBody.fromFile(
        path.join(
          __dirname,
          'step_function_templates',
          'update_database_on_new_samplesheet.asl.simple.json'
        )
      ),
      definitionSubstitutions: {
        __table_name__: props.tableObj.tableName,
        __table_partition_name__: this.updateDataBaseOnNewSamplesheetEventMap.tablePartition,
        __detail_type__: this.updateDataBaseOnNewSamplesheetEventMap.outputDetailType,
        __event_bus_name__: props.eventBusObj.eventBusName,
        __event_source__: this.updateDataBaseOnNewSamplesheetEventMap.outputSource,
        __decompress_samplesheet_function_arn__:
          decompressSamplesheetLambda.currentVersion.functionArn,
      },
    });

    /*
    Part 3: Wire up permissions
    */

    /* Allow state machine to write to the table */
    props.tableObj.grantReadWriteData(this.stateMachineObj);

    /* Allow state machine to invoke lambda */
    decompressSamplesheetLambda.currentVersion.grantInvoke(this.stateMachineObj.role);

    /* Allow state machine to send events */
    props.eventBusObj.grantPutEventsTo(this.stateMachineObj);

    /*
    Part 4: Build event rule
    */
    const eventRule = new events.Rule(this, 'update_database_on_new_samplesheet_event_rule', {
      eventBus: props.eventBusObj,
      eventPattern: {
        source: [this.updateDataBaseOnNewSamplesheetEventMap.triggerSource],
        detailType: [this.updateDataBaseOnNewSamplesheetEventMap.triggerDetailType],
        detail: {
          status: [this.updateDataBaseOnNewSamplesheetEventMap.triggerStatus],
          workflowName: [this.updateDataBaseOnNewSamplesheetEventMap.triggerWorkflowName],
        },
      },
    });
  }
}
